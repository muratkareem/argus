import csv
import io
import json
import logging
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal

import pandas as pd
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Integer, case, cast, func, or_, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.benchmarks import catalog
from app.config import Settings
from app.data import ingest
from app.db import (
    Case,
    CaseEntity,
    CaseEvent,
    CaseTransaction,
    Dataset,
    Entity,
    Note,
    Relationship,
    Transaction,
    connect,
    iso_utc,
    migrate,
)
from app.intelligence import AdvancedFilters, advanced_where, intelligence_router, timeline
from app.ml import FEATURES, Predictor, validate_frame

STATUSES = Literal["Open", "In Review", "Escalated", "Resolved", "False Positive"]
PRIORITIES = Literal["Low", "Medium", "High", "Critical"]
logger = logging.getLogger("argus.api")


class PredictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    features: dict[str, float]
    provenance: Literal["ulb", "synthetic"]
    threshold: float | None = Field(default=None, ge=0, le=1)
    transaction_id: str | int | None = None

    @field_validator("features")
    @classmethod
    def valid_features(cls, value):
        if set(value) != set(FEATURES):
            raise ValueError("Prediction requires exactly Time, Amount and V1–V28")
        validate_frame(pd.DataFrame([value]))
        return value


class BatchTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str | int | None = None
    features: dict[str, float]


class BatchPredictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    transactions: list[BatchTransaction] = Field(min_length=1, max_length=1000)
    provenance: Literal["ulb", "synthetic"]
    threshold: float | None = Field(default=None, ge=0, le=1)

    @field_validator("transactions")
    @classmethod
    def valid_transactions(cls, value):
        if any(set(item.features) != set(FEATURES) for item in value):
            raise ValueError("Every transaction requires exactly Time, Amount and V1–V28")
        validate_frame(pd.DataFrame([item.features for item in value]))
        return value


def risk_category(score):
    """Display bands for uncalibrated estimates, independent of review threshold."""
    return (
        "critical"
        if score >= 0.9
        else "high"
        if score >= 0.5
        else "medium"
        if score >= 0.1
        else "low"
    )


def prediction_json(bundle, score, provenance, threshold=None, transaction_id=None):
    threshold = bundle["threshold"] if threshold is None else threshold
    flagged = bool(score >= threshold)
    estimator = bundle["model"]
    if hasattr(estimator, "steps"):
        estimator = estimator.steps[-1][1]
    return {
        "transaction_id": transaction_id,
        "model_version": bundle["version"],
        "model_name": bundle.get("model_name", type(estimator).__name__),
        "risk_score": float(score),
        "fraud_probability": float(score),
        "predicted_class": int(flagged),
        "classification": "flagged" if flagged else "clear",
        "risk_category": risk_category(score),
        "decision_threshold": threshold,
        "provenance": provenance,
        "probability_type": "uncalibrated model class probability; not real-world certainty",
    }


class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    priority: PRIORITIES = "Medium"
    transaction_ids: list[int] = Field(default_factory=list, max_length=100)
    entity_ids: list[str] = Field(default_factory=list, max_length=100)


class CaseUpdate(BaseModel):
    status: STATUSES | None = None
    priority: PRIORITIES | None = None
    decision: str | None = Field(default=None, max_length=10000)


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)


class LinkInput(BaseModel):
    transaction_id: int = Field(gt=0)


def transaction_json(tx, provenance):
    return {
        "id": tx.id,
        "dataset_id": tx.dataset_id,
        "provenance": provenance,
        "amount": tx.amount,
        "time": tx.time,
        "label": tx.label,
        "risk_score": tx.risk_score,
        "flagged": bool(tx.flagged) if tx.flagged is not None else None,
        "threshold": tx.threshold,
        "model_version": tx.model_version,
    }


def case_json(session, case):
    return {
        "id": case.id,
        "title": case.title,
        "status": case.status,
        "priority": case.priority,
        "decision": case.decision,
        "created_at": iso_utc(case.created_at),
        "transaction_ids": list(
            session.scalars(
                select(CaseTransaction.transaction_id).where(CaseTransaction.case_id == case.id)
            )
        ),
        "entity_ids": list(
            session.scalars(select(CaseEntity.entity_id).where(CaseEntity.case_id == case.id))
        ),
        "notes": [
            {"id": n.id, "body": n.body, "created_at": iso_utc(n.created_at)}
            for n in session.scalars(select(Note).where(Note.case_id == case.id).order_by(Note.id))
        ],
    }


def create_app(settings=None):
    settings = settings or Settings()
    engine, factory = connect(settings.database_url)
    predictor = Predictor(settings.artifact_dir)

    @asynccontextmanager
    async def lifespan(app):
        migrate(engine)
        try:
            predictor.load()
        except (FileNotFoundError, ValueError, KeyError, OSError):
            logger.info("Active model unavailable; prediction endpoints will report model status")
        yield
        engine.dispose()

    app = FastAPI(title="ARGUS", version="0.1.0", lifespan=lifespan)
    app.state.session_factory, app.state.predictor = factory, predictor
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.middleware("http")
    async def request_boundary(request, call_next):
        started = time.perf_counter()
        request_id = uuid.uuid4().hex
        key = settings.api_key.get_secret_value() if settings.api_key else None
        if (
            key
            and request.url.path.startswith("/api/v1/")
            and request.url.path != "/api/v1/health"
            and request.method != "OPTIONS"
        ):
            supplied = request.headers.get("Authorization", "")
            if not secrets.compare_digest(supplied.encode(), f"Bearer {key}".encode()):
                return JSONResponse(
                    {"detail": "A valid API key is required"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                }
            )
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, exc):
        # Do not echo arbitrary request contents or non-finite floats into JSON errors.
        return JSONResponse(
            {"detail": [{k: e[k] for k in ("loc", "msg", "type")} for e in exc.errors()]},
            status_code=422,
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_request, exc):
        logger.error("Database operation failed: %s", type(exc).__name__)
        return JSONResponse(
            {"detail": "Database operation unavailable; retry or inspect local service health"},
            status_code=503,
        )

    def db():
        with factory() as session:
            yield session

    def require(session, cls, id):
        obj = session.get(cls, id)
        if obj is None:
            raise HTTPException(404, f"{cls.__name__} not found")
        return obj

    app.include_router(intelligence_router(db))

    def active_model_info():
        try:
            bundle = predictor.load()
            report_path = settings.artifact_dir / bundle["version"] / "report.json"
            report = json.loads(report_path.read_text()) if report_path.exists() else {}
            return {
                "status": "ready",
                "name": bundle.get("model_name"),
                "version": bundle["version"],
                "provenance": bundle["provenance"],
                "threshold": bundle["threshold"],
                "last_evaluated_at": report.get("created_at"),
                "probability_type": "uncalibrated model class probability",
            }
        except (FileNotFoundError, ValueError, KeyError, OSError):
            return {"status": "unavailable", "name": None, "version": None}

    def prediction(features, provenance, threshold=None, transaction_id=None):
        started = time.perf_counter()
        try:
            bundle, score = predictor.predict(pd.DataFrame([features]), provenance)
        except FileNotFoundError:
            raise HTTPException(503, "No trained model. Run the documented training command.")
        except ValueError as exc:
            raise HTTPException(409, str(exc))
        return {
            **prediction_json(bundle, score[0], provenance, threshold, transaction_id),
            "metadata": {
                "processing_ms": round((time.perf_counter() - started) * 1000, 3),
                "score_type": "uncalibrated model score",
                "features": len(FEATURES),
            },
        }

    @app.get("/api/v1/health")
    def health(session: Session = Depends(db)):
        session.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": engine.dialect.name,
            "research_prototype": True,
            "model_status": active_model_info()["status"],
        }

    @app.get("/api/v1/ready")
    def ready(session: Session = Depends(db)):
        session.execute(text("SELECT 1"))
        model = active_model_info()
        if model["status"] != "ready":
            raise HTTPException(
                503, "Database is healthy; train or restore a trusted model artifact"
            )
        return {"status": "ready", "model": model}

    @app.post("/api/v1/predict")
    def predict(data: PredictInput):
        return prediction(data.features, data.provenance, data.threshold, data.transaction_id)

    @app.post("/api/v1/predict/batch")
    def predict_batch(data: BatchPredictInput):
        started = time.perf_counter()
        try:
            bundle, scores = predictor.predict(
                pd.DataFrame([item.features for item in data.transactions]), data.provenance
            )
        except FileNotFoundError:
            raise HTTPException(503, "No trained model. Run the documented training command.")
        except ValueError as exc:
            raise HTTPException(409, str(exc))
        return {
            "items": [
                prediction_json(bundle, score, data.provenance, data.threshold, item.id)
                for item, score in zip(data.transactions, scores)
            ],
            "count": len(scores),
            "model_version": bundle["version"],
            "processing_ms": round((time.perf_counter() - started) * 1000, 3),
        }

    @app.post("/api/v1/predict/explanation")
    def explain_prediction(data: PredictInput):
        try:
            return predictor.explain(data.features, data.provenance)
        except FileNotFoundError:
            raise HTTPException(503, "Train a matching model before requesting an explanation")
        except ValueError as exc:
            raise HTTPException(409, str(exc))

    @app.get("/api/v1/datasets")
    def datasets(session: Session = Depends(db)):
        return [
            {
                "id": d.id,
                "name": d.name,
                "provenance": d.provenance,
                "rows": d.rows,
                "duplicates": d.duplicates,
                "created_at": iso_utc(d.created_at),
                "audit": d.audit or {},
            }
            for d in session.scalars(select(Dataset).order_by(Dataset.id.desc()))
        ]

    @app.post("/api/v1/datasets/upload")
    async def upload(
        file: UploadFile = File(...),
        provenance: Literal["ulb", "synthetic"] = Form(...),
        session: Session = Depends(db),
    ):
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(422, "Upload a .csv file")
        content = await file.read(settings.max_upload_bytes + 1)
        await file.close()
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                413, f"CSV exceeds {settings.max_upload_bytes // 1024**2} MiB limit"
            )
        try:
            return await run_in_threadpool(
                ingest, session, content, file.filename, provenance, predictor
            )
        except ValueError as exc:
            session.rollback()
            raise HTTPException(422, str(exc))
        except IntegrityError:
            session.rollback()
            raise HTTPException(409, "Concurrent duplicate upload; retry the import")

    @app.post("/api/v1/datasets/{dataset_id}/score")
    def batch_score(dataset_id: int, session: Session = Depends(db)):
        dataset = require(session, Dataset, dataset_id)
        count, last_id, version = 0, 0, None
        while True:
            chunk = session.execute(
                select(Transaction.id, Transaction.features)
                .where(Transaction.dataset_id == dataset_id, Transaction.id > last_id)
                .order_by(Transaction.id)
                .limit(2000)
            ).all()
            if not chunk:
                break
            try:
                bundle, scores = predictor.predict(
                    pd.DataFrame([r.features for r in chunk]), dataset.provenance
                )
            except FileNotFoundError:
                raise HTTPException(503, "Train a matching model first")
            except ValueError as exc:
                raise HTTPException(409, str(exc))
            if version is not None and version != bundle["version"]:
                session.rollback()
                raise HTTPException(409, "Active model changed during scoring; retry the batch")
            version = bundle["version"]
            session.execute(
                update(Transaction),
                [
                    {
                        "id": tx.id,
                        "risk_score": float(score),
                        "flagged": int(score >= bundle["threshold"]),
                        "model_version": version,
                        "threshold": bundle["threshold"],
                    }
                    for tx, score in zip(chunk, scores)
                ],
            )
            last_id = chunk[-1].id
            count += len(chunk)
        session.commit()
        return {"scored": count, "model_version": version}

    def transaction_query(q, flagged, provenance, min_risk):
        query = select(Transaction, Dataset.provenance).join(Dataset)
        if q:
            query = query.where(
                or_(
                    Transaction.id == int(q) if q.isdigit() else False, Dataset.name.ilike(f"%{q}%")
                )
            )
        if flagged is not None:
            query = query.where(Transaction.flagged == int(flagged))
        if provenance:
            query = query.where(Dataset.provenance == provenance)
        if min_risk is not None:
            query = query.where(Transaction.risk_score >= min_risk)
        return query

    @app.get("/api/v1/transactions/export")
    def export_transactions(
        format: Literal["csv", "json"] = "csv",
        q: str = "",
        flagged: bool | None = None,
        provenance: Literal["ulb", "synthetic"] | None = None,
        min_risk: float | None = Query(None, ge=0, le=1),
        extra: AdvancedFilters = Depends(),
        session: Session = Depends(db),
    ):
        rows = [
            transaction_json(tx, p)
            for tx, p in session.execute(
                advanced_where(
                    transaction_query(q, flagged, provenance, min_risk), extra, min_risk
                ).order_by(Transaction.id)
            )
        ]
        if format == "json":
            return {
                "exported_at": pd.Timestamp.now(tz="UTC").isoformat(),
                "disclaimer": "Research prototype; uncalibrated scores",
                "transactions": rows,
            }
        stream = io.StringIO()
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "id",
                "dataset_id",
                "provenance",
                "amount",
                "time",
                "label",
                "risk_score",
                "flagged",
                "threshold",
                "model_version",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
        return Response(
            stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="argus-transactions.csv"'},
        )

    @app.get("/api/v1/transactions")
    def transactions(
        q: str = Query("", max_length=200),
        flagged: bool | None = None,
        provenance: Literal["ulb", "synthetic"] | None = None,
        min_risk: float | None = Query(None, ge=0, le=1),
        extra: AdvancedFilters = Depends(),
        sort: Literal["id", "amount", "risk_score", "time"] = "risk_score",
        direction: Literal["asc", "desc"] = "desc",
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(db),
    ):
        query = advanced_where(transaction_query(q, flagged, provenance, min_risk), extra, min_risk)
        total = session.scalar(select(func.count()).select_from(query.subquery()))
        column = getattr(Transaction, sort)
        order = column.asc().nulls_last() if direction == "asc" else column.desc().nulls_last()
        rows = session.execute(
            query.order_by(order, Transaction.id).offset((page - 1) * page_size).limit(page_size)
        )
        return {
            "items": [transaction_json(tx, p) for tx, p in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @app.get("/api/v1/transactions/{id}")
    def transaction(id: int, session: Session = Depends(db)):
        tx = require(session, Transaction, id)
        return {
            **transaction_json(tx, require(session, Dataset, tx.dataset_id).provenance),
            "features": tx.features,
            "case_ids": list(
                session.scalars(
                    select(CaseTransaction.case_id).where(CaseTransaction.transaction_id == id)
                )
            ),
        }

    @app.get("/api/v1/transactions/{id}/explanation")
    def explanation(id: int, session: Session = Depends(db)):
        tx = require(session, Transaction, id)
        try:
            result = predictor.explain(
                tx.features, require(session, Dataset, tx.dataset_id).provenance
            )
            result["stored_model_version"] = tx.model_version
            result["matches_stored_prediction"] = tx.model_version == result["model_version"]
            return result
        except FileNotFoundError:
            raise HTTPException(503, "Train a model first")
        except ValueError as exc:
            raise HTTPException(409, str(exc))

    @app.get("/api/v1/overview")
    def overview(session: Session = Depends(db)):
        total, scored, flagged, volume, labeled_fraud, labeled_legitimate = session.execute(
            select(
                func.count(Transaction.id),
                func.count(Transaction.risk_score),
                func.coalesce(func.sum(Transaction.flagged), 0),
                func.coalesce(func.sum(Transaction.amount), 0),
                func.coalesce(func.sum(case((Transaction.label == 1, 1), else_=0)), 0),
                func.coalesce(func.sum(case((Transaction.label == 0, 1), else_=0)), 0),
            )
        ).one()
        fraud_count, detected = session.execute(
            select(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.flagged), 0),
            ).where(Transaction.label == 1, Transaction.flagged.is_not(None))
        ).one()
        provenance_counts = dict(
            session.execute(
                select(Dataset.provenance, func.count(Transaction.id))
                .join(Transaction, Transaction.dataset_id == Dataset.id)
                .group_by(Dataset.provenance)
            ).all()
        )
        bucket = case(
            (Transaction.risk_score >= 1, 9),
            else_=cast(func.floor(Transaction.risk_score * 10), Integer),
        )
        counts = dict(
            session.execute(
                select(bucket, func.count(Transaction.id))
                .where(Transaction.risk_score.is_not(None))
                .group_by(bucket)
            ).all()
        )
        hour = cast(func.floor(Transaction.time / 3600), Integer)
        trend = [
            {"hour": h, "count": n, "flagged": f, "amount": float(a)}
            for h, n, f, a in session.execute(
                select(
                    hour,
                    func.count(Transaction.id),
                    func.coalesce(func.sum(Transaction.flagged), 0),
                    func.sum(Transaction.amount),
                )
                .group_by(hour)
                .order_by(hour)
            )
        ]
        recent = session.execute(
            select(Transaction, Dataset.provenance)
            .join(Dataset)
            .where(Transaction.flagged == 1)
            .order_by(Transaction.id.desc())
            .limit(8)
        )
        return {
            "total": total,
            "scored": scored,
            "flagged": flagged,
            "volume": round(float(volume), 2),
            "fraud_detection_rate": detected / fraud_count if fraud_count else None,
            "labeled_scored_fraud": fraud_count,
            "labeled_fraud": labeled_fraud,
            "labeled_legitimate": labeled_legitimate,
            "unlabeled": total - labeled_fraud - labeled_legitimate,
            "provenance_counts": provenance_counts,
            "risk_distribution": [
                {"bucket": f"{i * 10}–{(i + 1) * 10}%", "count": counts.get(i, 0)}
                for i in range(10)
            ],
            "trend": trend,
            "recent_flagged": [transaction_json(t, p) for t, p in recent],
            "open_cases": session.scalar(
                select(func.count())
                .select_from(Case)
                .where(Case.status.in_(["Open", "In Review", "Escalated"]))
            ),
        }

    @app.get("/api/v1/benchmarks")
    def benchmarks():
        return catalog(settings.benchmark_dir)

    @app.get("/api/v1/models")
    def models():
        reports = []
        for path in sorted(settings.artifact_dir.glob("*/report.json"), reverse=True):
            reports.append(json.loads(path.read_text()))
        active = (
            json.loads((settings.artifact_dir / "current.json").read_text())["version"]
            if (settings.artifact_dir / "current.json").exists()
            else None
        )
        return {"active_version": active, "experiments": reports}

    @app.get("/api/v1/cases")
    def cases(q: str = Query("", max_length=200), session: Session = Depends(db)):
        query = (
            select(Case)
            .where(
                or_(
                    Case.title.ilike(f"%{q}%"),
                    Case.decision.ilike(f"%{q}%"),
                    Case.id.in_(select(Note.case_id).where(Note.body.ilike(f"%{q}%"))),
                )
            )
            .order_by(Case.id.desc())
        )
        return [case_json(session, c) for c in session.scalars(query)]

    @app.post("/api/v1/cases", status_code=201)
    def create_case(data: CaseCreate, session: Session = Depends(db)):
        for id in set(data.transaction_ids):
            require(session, Transaction, id)
        for entity_id in set(data.entity_ids):
            require(session, Entity, entity_id)
        case = Case(title=data.title, priority=data.priority)
        session.add(case)
        session.flush()
        session.add_all(
            [
                CaseTransaction(case_id=case.id, transaction_id=id)
                for id in set(data.transaction_ids)
            ]
        )
        session.add_all([CaseEntity(case_id=case.id, entity_id=e) for e in set(data.entity_ids)])
        session.commit()
        return case_json(session, case)

    @app.get("/api/v1/cases/{id}")
    def get_case(id: int, session: Session = Depends(db)):
        return case_json(session, require(session, Case, id))

    @app.patch("/api/v1/cases/{id}")
    def update_case(id: int, data: CaseUpdate, session: Session = Depends(db)):
        case = require(session, Case, id)
        for key, value in data.model_dump(exclude_none=True).items():
            previous = getattr(case, key)
            if previous != value:
                session.add(
                    CaseEvent(
                        case_id=id,
                        kind=f"{key}_changed",
                        payload={"before": previous, "after": value},
                    )
                )
                setattr(case, key, value)
        session.commit()
        return case_json(session, case)

    @app.post("/api/v1/cases/{id}/transactions")
    def link_case(id: int, data: LinkInput, session: Session = Depends(db)):
        case = require(session, Case, id)
        require(session, Transaction, data.transaction_id)
        if not session.get(CaseTransaction, (id, data.transaction_id)):
            session.add(CaseTransaction(case_id=id, transaction_id=data.transaction_id))
            session.add(
                CaseEvent(
                    case_id=id,
                    kind="transaction_linked",
                    payload={"transaction_id": data.transaction_id},
                )
            )
            session.commit()
        return case_json(session, case)

    @app.post("/api/v1/cases/{id}/notes", status_code=201)
    def add_note(id: int, data: NoteCreate, session: Session = Depends(db)):
        case = require(session, Case, id)
        session.add(Note(case_id=id, body=data.body))
        session.commit()
        return case_json(session, case)

    @app.get("/api/v1/cases/{id}/export")
    def export_case(id: int, session: Session = Depends(db)):
        case = case_json(session, require(session, Case, id))
        txs = []
        for txid in case["transaction_ids"]:
            tx = require(session, Transaction, txid)
            txs.append(transaction_json(tx, require(session, Dataset, tx.dataset_id).provenance))
        return {
            "exported_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "case": case,
            "timeline": timeline(session, require(session, Case, id)),
            "entities": [
                {"id": e.id, "kind": e.kind, "label": e.label, "provenance": "synthetic"}
                for e in session.scalars(select(Entity).where(Entity.id.in_(case["entity_ids"])))
            ],
            "transactions": txs,
            "disclaimer": "Research prototype. Analyst notes are opinions; scores are uncalibrated. Synthetic records are artificial.",
        }

    @app.get("/api/v1/graph")
    def graph(kind: str | None = None, session: Session = Depends(db)):
        entities = list(session.scalars(select(Entity)))
        ids = {e.id for e in entities if not kind or e.kind == kind}
        edges = list(session.scalars(select(Relationship)))
        return {
            "provenance": "synthetic",
            "disclaimer": "Separate artificial relationships; no ULB or scored transaction links.",
            "nodes": [
                {"data": {"id": e.id, "label": e.label, "kind": e.kind}}
                for e in entities
                if e.id in ids
            ],
            "edges": [
                {"data": {"id": str(e.id), "source": e.source, "target": e.target, "label": e.kind}}
                for e in edges
                if e.source in ids and e.target in ids
            ],
        }

    @app.get("/api/v1/settings")
    def get_settings():
        return {
            "database": engine.dialect.name,
            "max_upload_mib": settings.max_upload_bytes // 1024**2,
            "authentication": "Bearer API key"
            if settings.api_key
            else "None; local research use only",
            "schema": FEATURES + ["Class (optional)"],
            "feature_schema": FEATURES,
            "max_batch_size": 1000,
            "active_model": active_model_info(),
            "risk_bands": {
                "low": "[0, 0.1)",
                "medium": "[0.1, 0.5)",
                "high": "[0.5, 0.9)",
                "critical": "[0.9, 1]",
            },
        }

    return app


app = create_app()
