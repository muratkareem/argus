from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    provenance = Column(String(30), nullable=False)
    rows = Column(Integer, nullable=False)
    duplicates = Column(Integer, nullable=False, default=0)
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
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
        pool_pre_ping=True,
    )
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
