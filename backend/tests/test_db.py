from concurrent.futures import ThreadPoolExecutor

import pytest
from app.db import Base, Dataset, SchemaMigration, Transaction, connect, migrate
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError


def test_sqlite_enforces_foreign_keys_and_configures_concurrent_readers(tmp_path):
    engine, factory = connect(f"sqlite:///{tmp_path}/integrity.db")
    Base.metadata.create_all(engine)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
            assert connection.scalar(text("PRAGMA busy_timeout")) == 30000
            assert connection.scalar(text("PRAGMA journal_mode")) == "wal"
        with factory() as session:
            session.add(
                Transaction(dataset_id=999, fingerprint="a" * 64, features={}, amount=1, time=1)
            )
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()
            session.add(Dataset(name="committed", provenance="synthetic", rows=0))
            session.commit()
        with factory() as writer:
            writer.add(Dataset(name="pending", provenance="synthetic", rows=0))
            writer.flush()

            def read_committed():
                with factory() as reader:
                    return list(reader.scalars(select(Dataset.name)))

            with ThreadPoolExecutor(max_workers=1) as pool:
                assert pool.submit(read_committed).result(timeout=3) == ["committed"]
            writer.rollback()
    finally:
        engine.dispose()


def test_sqlite_memory_database_is_visible_across_worker_threads():
    engine, factory = connect("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with factory() as session:
            session.add(Dataset(name="shared", provenance="synthetic", rows=0))
            session.commit()

        def read():
            with factory() as session:
                return session.scalar(select(Dataset.name))

        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(read).result(timeout=3) == "shared"
    finally:
        engine.dispose()


def test_additive_migrations_preserve_populated_legacy_database(tmp_path):
    engine, factory = connect(f"sqlite:///{tmp_path}/legacy.db")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE datasets (id INTEGER PRIMARY KEY, name VARCHAR(200) NOT NULL, provenance VARCHAR(30) NOT NULL, rows INTEGER NOT NULL, duplicates INTEGER NOT NULL, created_at DATETIME)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO datasets VALUES (1, 'Existing research', 'ulb', 5, 2, '2026-01-01 00:00:00')"
                )
            )
        migrate(engine)
        migrate(engine)
        with factory() as session:
            dataset = session.get(Dataset, 1)
            assert dataset.name == "Existing research"
            assert dataset.rows == 5 and dataset.duplicates == 2
            assert dataset.audit is None
            assert list(
                session.scalars(select(SchemaMigration.version).order_by(SchemaMigration.version))
            ) == [1, 2]
        indexes = {index["name"] for index in inspect(engine).get_indexes("datasets")}
        assert "ix_datasets_provenance_id" in indexes
        indexes = {index["name"] for index in inspect(engine).get_indexes("transactions")}
        assert {
            "ix_transactions_amount_id",
            "ix_transactions_flagged_risk_id",
            "ix_transactions_dataset_risk_id",
        } <= indexes
    finally:
        engine.dispose()


def test_filtered_pagination_uses_composite_index(tmp_path):
    engine, _ = connect(f"sqlite:///{tmp_path}/plan.db")
    try:
        migrate(engine)
        with engine.connect() as connection:
            plan = connection.execute(
                text(
                    "EXPLAIN QUERY PLAN SELECT id, risk_score FROM transactions WHERE flagged=1 ORDER BY risk_score DESC NULLS LAST, id ASC LIMIT 20"
                )
            ).all()
        details = " ".join(str(row) for row in plan)
        assert "ix_transactions_flagged_risk_id" in details
        assert "TEMP B-TREE" not in details
    finally:
        engine.dispose()
