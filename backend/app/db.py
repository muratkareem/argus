from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    event,
    inspect,
    select,
    text,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


def now():
    return datetime.now(timezone.utc)


def iso_utc(value):
    """SQLite drops tzinfo; all ARGUS timestamps are stored/generated in UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    provenance = Column(String(30), nullable=False)
    rows = Column(Integer, nullable=False)
    duplicates = Column(Integer, nullable=False, default=0)
    audit = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    dataset_id = Column(ForeignKey("datasets.id"), nullable=False, index=True)
    fingerprint = Column(String(64), nullable=False, unique=True)
    features = Column(JSON, nullable=False)
    amount = Column(Float, nullable=False)
    time = Column(Float, nullable=False)
    label = Column(Integer, nullable=True)
    risk_score = Column(Float, nullable=True, index=True)
    flagged = Column(Integer, nullable=True)
    model_version = Column(String(100), nullable=True)
    threshold = Column(Float, nullable=True)


class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    status = Column(String(30), default="Open", nullable=False)
    priority = Column(String(20), default="Medium", nullable=False)
    decision = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)


class CaseTransaction(Base):
    __tablename__ = "case_transactions"
    case_id = Column(ForeignKey("cases.id"), primary_key=True)
    transaction_id = Column(ForeignKey("transactions.id"), primary_key=True)


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True)
    case_id = Column(ForeignKey("cases.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)


class Entity(Base):
    __tablename__ = "entities"
    id = Column(String(80), primary_key=True)
    kind = Column(String(30), nullable=False)
    label = Column(String(100), nullable=False)


class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(Integer, primary_key=True)
    source = Column(ForeignKey("entities.id"), nullable=False)
    target = Column(ForeignKey("entities.id"), nullable=False)
    kind = Column(String(40), nullable=False)


def connect(url):
    sqlite = url.startswith("sqlite")
    options = {}
    if sqlite and (url.endswith(":memory:") or url in {"sqlite://", "sqlite+pysqlite://"}):
        # One connection keeps an in-memory database visible to worker threads.
        options["poolclass"] = StaticPool
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False, "timeout": 30} if sqlite else {},
        pool_pre_ping=True,
        **options,
    )
    if sqlite:

        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _record):
            cursor = connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA busy_timeout=30000")
                # WAL lets dashboard readers proceed during a bounded import write.
                # SQLite leaves in-memory databases in their supported memory mode.
                cursor.execute("PRAGMA journal_mode=WAL")
            finally:
                cursor.close()

    return engine, sessionmaker(bind=engine, expire_on_commit=False)


class SavedView(Base):
    __tablename__ = "saved_views"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    filters = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)


class CaseEvent(Base):
    __tablename__ = "case_events"
    id = Column(Integer, primary_key=True)
    case_id = Column(ForeignKey("cases.id"), nullable=False, index=True)
    kind = Column(String(40), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)


class CaseEntity(Base):
    __tablename__ = "case_entities"
    case_id = Column(ForeignKey("cases.id"), primary_key=True)
    entity_id = Column(ForeignKey("entities.id"), primary_key=True)


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"
    version = Column(Integer, primary_key=True)
    applied_at = Column(DateTime(timezone=True), default=now, nullable=False)


# Match common filtering and deterministic pagination rather than indexing JSON.
Index("ix_datasets_provenance_id", Dataset.provenance, Dataset.id)
Index("ix_transactions_amount_id", Transaction.amount, Transaction.id)
Index("ix_transactions_time_id", Transaction.time, Transaction.id)
Index(
    "ix_transactions_flagged_risk_id",
    Transaction.flagged,
    Transaction.risk_score.desc(),
    Transaction.id,
)
Index(
    "ix_transactions_dataset_risk_id",
    Transaction.dataset_id,
    Transaction.risk_score.desc(),
    Transaction.id,
)
Index("ix_relationships_source", Relationship.source)
Index("ix_relationships_target", Relationship.target)
Index("ix_case_entities_entity_case", CaseEntity.entity_id, CaseEntity.case_id)


def migrate(engine):
    """Idempotent additive migrations for existing SQLite/PostgreSQL workspaces.

    Existing records and model files remain intact. Run one migration process
    before starting application workers; table creation alone cannot add columns
    or indexes to tables that already exist.
    """
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        applied = set(connection.scalars(select(SchemaMigration.version)))
        if 1 not in applied:
            columns = {column["name"] for column in inspect(connection).get_columns("datasets")}
            if "audit" not in columns:
                connection.execute(text("ALTER TABLE datasets ADD COLUMN audit JSON"))
            connection.execute(SchemaMigration.__table__.insert().values(version=1))
        if 2 not in applied:
            for table in Base.metadata.sorted_tables:
                for index in table.indexes:
                    index.create(connection, checkfirst=True)
            connection.execute(SchemaMigration.__table__.insert().values(version=2))
