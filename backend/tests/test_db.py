from concurrent.futures import ThreadPoolExecutor

import pytest
from app.db import Base, Dataset, Transaction, connect
from sqlalchemy import select, text
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
            session.add(Transaction(dataset_id=999, fingerprint="a" * 64, features={}, amount=1, time=1))
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
