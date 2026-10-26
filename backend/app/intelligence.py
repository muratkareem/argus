"""Additive analyst capabilities: existing datasets/models/tables are never rewritten."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import (
    Case,
    CaseEntity,
    CaseEvent,
    Dataset,
    Entity,
    Note,
    Relationship,
    SavedView,
    Transaction,
    iso_utc,
)


class AdvancedFilters(BaseModel):
    max_risk: float | None = Field(None, ge=0, le=1)
    min_amount: float | None = Field(None, ge=0)
    max_amount: float | None = Field(None, ge=0)
    min_time: float | None = Field(None, ge=0)
    max_time: float | None = Field(None, ge=0)
    label: int | None = Field(None, ge=0, le=1)
    dataset_id: int | None = Field(None, gt=0)


class FilterConfiguration(AdvancedFilters):
    model_config = ConfigDict(extra="forbid")
    q: str = Field("", max_length=200)
    flagged: bool | None = None
    provenance: str | None = Field(None, pattern="^(ulb|synthetic)$")
    min_risk: float | None = Field(None, ge=0, le=1)
    sort: str = Field("risk_score", pattern="^(id|amount|risk_score|time)$")
    direction: str = Field("desc", pattern="^(asc|desc)$")


class ViewCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    filters: FilterConfiguration


class EntityLink(BaseModel):
    entity_id: str = Field(min_length=1, max_length=80)


def advanced_where(query, extra, min_risk=None):
    for low, high in [
        (extra.min_amount, extra.max_amount),
        (extra.min_time, extra.max_time),
        (min_risk, extra.max_risk),
    ]:
        if low is not None and high is not None and low > high:
            raise HTTPException(422, "Filter minimum must not exceed maximum")
    for name, operator, value in [
        ("risk_score", "le", extra.max_risk),
        ("amount", "ge", extra.min_amount),
        ("amount", "le", extra.max_amount),
        ("time", "ge", extra.min_time),
        ("time", "le", extra.max_time),
        ("label", "eq", extra.label),
        ("dataset_id", "eq", extra.dataset_id),
    ]:
        if value is not None:
            column = getattr(Transaction, name)
            query = query.where(
                {"le": column.__le__, "ge": column.__ge__, "eq": column.__eq__}[operator](value)
            )
    return query


def timeline(session, case):
    events = [
        {
            "id": f"created-{case.id}",
            "kind": "created",
            "payload": {"title": case.title},
            "created_at": iso_utc(case.created_at),
        }
    ]
    events += [
        {
            "id": f"event-{e.id}",
            "kind": e.kind,
            "payload": e.payload,
            "created_at": iso_utc(e.created_at),
        }
        for e in session.scalars(select(CaseEvent).where(CaseEvent.case_id == case.id))
    ]
    events += [
        {
            "id": f"note-{n.id}",
            "kind": "note",
            "payload": {"body": n.body},
            "created_at": iso_utc(n.created_at),
        }
        for n in session.scalars(select(Note).where(Note.case_id == case.id))
    ]
    # SQLite and PostgreSQL timezone representations differ; compare actual timestamps.
    from datetime import datetime, timezone

    def stamp(event):
        value = datetime.fromisoformat(event["created_at"])
        return (
            value.replace(tzinfo=timezone.utc).timestamp()
            if value.tzinfo is None
            else value.timestamp()
        )

    return sorted(events, key=lambda e: (stamp(e), e["id"]))


def intelligence_router(db):
    router = APIRouter(prefix="/api/v1")

    def require(session, cls, id):
        obj = session.get(cls, id)
        if obj is None:
            raise HTTPException(404, f"{cls.__name__} not found")
        return obj

    @router.get("/search")
    def search(q: str = Query(..., min_length=1, max_length=120), session: Session = Depends(db)):
        pattern = f"%{q.strip()}%"
        token = q.upper().removeprefix("TX-").removeprefix("CASE-").lstrip("#")
        numeric = int(token) if token.isdigit() and len(token) <= 10 else -1
        rows = session.execute(
            select(Transaction.id, Transaction.risk_score, Dataset.provenance)
            .join(Dataset)
            .where(or_(Transaction.id == numeric, Dataset.name.ilike(pattern)))
            .order_by(Transaction.id.desc())
            .limit(8)
        )
        results = [
            {
                "kind": "Transaction",
                "id": str(id),
                "label": f"TX-{id:06d}",
                "detail": f"{source} · score {score:.3f}"
                if score is not None
                else f"{source} · unscored",
            }
            for id, score, source in rows
        ]
        results += [
            {
                "kind": "Case",
                "id": str(c.id),
                "label": c.title,
                "detail": f"Case #{c.id} · {c.status} · {c.priority}",
            }
            for c in session.scalars(
                select(Case)
                .where(or_(Case.title.ilike(pattern), Case.id == numeric))
                .order_by(Case.id.desc())
                .limit(8)
            )
        ]
        results += [
            {"kind": "Entity", "id": e.id, "label": e.label, "detail": f"Synthetic {e.kind}"}
            for e in session.scalars(
                select(Entity)
                .where(or_(Entity.id.ilike(pattern), Entity.label.ilike(pattern)))
                .limit(8)
            )
        ]
        return {"query": q, "results": results}

    @router.get("/views")
    def views(session: Session = Depends(db)):
        return [
            {"id": v.id, "name": v.name, "filters": v.filters}
            for v in session.scalars(select(SavedView).order_by(SavedView.id.desc()))
        ]

    @router.post("/views", status_code=201)
    def save_view(data: ViewCreate, session: Session = Depends(db)):
        advanced_where(select(Transaction), data.filters, data.filters.min_risk)
        view = SavedView(name=data.name, filters=data.filters.model_dump(exclude_none=True))
        session.add(view)
        session.commit()
        return {"id": view.id, "name": view.name, "filters": view.filters}

    @router.delete("/views/{id}")
    def delete_view(id: int, session: Session = Depends(db)):
        session.delete(require(session, SavedView, id))
        session.commit()
        return {"deleted": id}

    @router.get("/cases/{id}/timeline")
    def case_timeline(id: int, session: Session = Depends(db)):
        return timeline(session, require(session, Case, id))

    @router.post("/cases/{id}/entities")
    def link_entity(id: int, data: EntityLink, session: Session = Depends(db)):
        require(session, Case, id)
        entity = require(session, Entity, data.entity_id)
        if not session.get(CaseEntity, (id, entity.id)):
            session.add(CaseEntity(case_id=id, entity_id=entity.id))
            session.add(
                CaseEvent(
                    case_id=id,
                    kind="entity_linked",
                    payload={"entity_id": entity.id, "provenance": "synthetic"},
                )
            )
            session.commit()
        return {"case_id": id, "entity_id": entity.id, "provenance": "synthetic"}

    @router.get("/entities/{id}")
    def entity_detail(id: str, session: Session = Depends(db)):
        entity = require(session, Entity, id)
        edges = list(
            session.scalars(
                select(Relationship).where(
                    or_(Relationship.source == id, Relationship.target == id)
                )
            )
        )
        neighbors = {e.source if e.target == id else e.target for e in edges}
        return {
            "id": entity.id,
            "kind": entity.kind,
            "label": entity.label,
            "provenance": "synthetic",
            "neighbors": [
                {"id": e.id, "kind": e.kind, "label": e.label}
                for e in session.scalars(select(Entity).where(Entity.id.in_(neighbors)))
            ],
            "case_ids": list(
                session.scalars(select(CaseEntity.case_id).where(CaseEntity.entity_id == id))
            ),
        }

    @router.get("/intelligence/graph")
    def graph(
        root: str | None = None,
        depth: int = Query(1, ge=0, le=4),
        kind: str | None = None,
        relation: str | None = None,
        shared_only: bool = False,
        session: Session = Depends(db),
    ):
        entities = list(session.scalars(select(Entity)))
        all_edges = list(session.scalars(select(Relationship)))
        shares = dict(
            session.execute(
                select(Relationship.target, func.count(Relationship.source))
                .where(Relationship.kind == "uses")
                .group_by(Relationship.target)
            ).all()
        )
        edges = [e for e in all_edges if not relation or e.kind == relation]
        ids = {e.id for e in entities}
        if root:
            require(session, Entity, root)
            ids, frontier = {root}, {root}
            for _ in range(depth):
                adjacent = {e.target for e in edges if e.source in frontier} | {
                    e.source for e in edges if e.target in frontier
                }
                frontier = adjacent - ids
                ids |= frontier
        if shared_only:
            shared = {id for id, count in shares.items() if count > 1}
            ids &= shared | {e.source for e in edges if e.target in shared}
        if kind:
            ids &= {e.id for e in entities if e.kind == kind}
        return {
            "provenance": "synthetic",
            "root": root,
            "depth": depth,
            "nodes": [
                {
                    "data": {
                        "id": e.id,
                        "label": e.label,
                        "kind": e.kind,
                        "shared_accounts": shares.get(e.id, 0),
                    }
                }
                for e in entities
                if e.id in ids
            ],
            "edges": [
                {"data": {"id": str(e.id), "source": e.source, "target": e.target, "label": e.kind}}
                for e in edges
                if e.source in ids and e.target in ids
            ],
            "total_entities": len(entities),
            "disclaimer": "Synthetic structure only; shared devices are an investigative cue, not a fraud determination.",
        }

    return router
