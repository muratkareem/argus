"""Bounded read-only evidence assembly. This module has no write or tool execution path."""

from fastapi import HTTPException
from sqlalchemy import select

from app.db import Case, Dataset, Entity, Transaction


def prepare_context(session, predictor, transaction_id, case_id, transaction_json, case_json):
    if not transaction_id and not case_id:
        raise HTTPException(422, "Select a transaction or investigation for read-only evidence")
    evidence, sources = {}, []

    def add_transaction(id):
        tx = session.get(Transaction, id)
        if tx is None:
            raise HTTPException(404, "Transaction not found")
        source = session.get(Dataset, tx.dataset_id).provenance
        item = {**transaction_json(tx, source), "source_id": f"transaction:{tx.id}"}
        sources.append(
            {
                "id": item["source_id"],
                "kind": "Transaction",
                "label": f"TX-{tx.id:06d}",
                "provenance": source,
                "model_version": tx.model_version,
            }
        )
        return tx, item

    if transaction_id:
        tx, evidence["database_transaction"] = add_transaction(transaction_id)
        try:
            explanation = predictor.explain(
                tx.features, evidence["database_transaction"]["provenance"]
            )
            evidence["model_explanation"] = {
                k: explanation[k]
                for k in ["method", "model_version", "base_value", "output_space", "caveat"]
            }
            evidence["model_explanation"]["top_features"] = explanation["features"][:5]
            evidence["model_explanation"]["matches_stored_prediction"] = (
                tx.model_version == explanation["model_version"]
            )
        except (FileNotFoundError, ValueError):
            evidence["explanation_status"] = (
                "No compatible active model explanation; do not infer one."
            )
    if case_id:
        case = session.get(Case, case_id)
        if case is None:
            raise HTTPException(404, "Case not found")
        record = case_json(session, case)
        record["notes_total"] = len(record["notes"])
        record["notes"] = [{**n, "body": n["body"][:800]} for n in record["notes"][-4:]]
        record["decision"] = record["decision"][:1500]
        record["context_limits"] = (
            "Latest 4 notes (800 characters each), first 8 transaction links, first 4 synthetic entities; full evidence remains in database."
        )
        evidence["analyst_case"] = record
        sources.append(
            {
                "id": f"case:{case.id}",
                "kind": "Case",
                "label": case.title,
                "provenance": "analyst record",
            }
        )
        evidence["case_transactions"] = [
            add_transaction(id)[1] for id in record["transaction_ids"][:8] if id != transaction_id
        ]
        evidence["synthetic_entities"] = [
            {
                "id": e.id,
                "label": e.label,
                "kind": e.kind,
                "provenance": "synthetic",
                "source_id": f"entity:{e.id}",
            }
            for e in session.scalars(select(Entity).where(Entity.id.in_(record["entity_ids"][:4])))
        ]
        sources += [
            {"id": e["source_id"], "kind": "Entity", "label": e["label"], "provenance": "synthetic"}
            for e in evidence["synthetic_entities"]
        ]
    return {
        "evidence": evidence,
        "sources": sources,
        "scope": {"transaction_id": transaction_id, "case_id": case_id},
        "boundary": "Read-only records. Case links are analyst associations, not model evidence of causality. Synthetic graph entities establish no ULB relationships.",
    }


def output_schema(sources):
    return {
        "type": "object",
        "properties": {
            **{
                key: {"type": "string"}
                for key in ["recorded_facts", "model_output", "uncertainty", "next_steps"]
            },
            "citations": {
                "type": "array",
                "items": {"type": "string", "enum": [s["id"] for s in sources]},
                "minItems": 1,
            },
        },
        "required": ["recorded_facts", "model_output", "uncertainty", "next_steps", "citations"],
        "additionalProperties": False,
    }


def render_interpretation(content, sources):
    import json
    import re

    known = {s["id"] for s in sources}
    if content.lstrip().startswith("{"):
        try:
            sections = json.loads(content)
            keys = ["recorded_facts", "model_output", "uncertainty", "next_steps"]
            if not all(isinstance(sections.get(key), str) for key in keys):
                raise ValueError("Missing structured sections")
            citations = sections.get("citations", [])
            if (
                not citations
                or not isinstance(citations, list)
                or not all(isinstance(id, str) and id in known for id in citations)
            ):
                raise ValueError("Unknown or absent source IDs")
            text = "\n\n".join(f"{key.replace('_', ' ').title()}\n{sections[key]}" for key in keys)
            text += "\n\nSources: " + " ".join(f"[{id}]" for id in citations)
            return text, {"status": "validated_ids", "cited_ids": citations}
        except (ValueError, TypeError) as exc:
            raise HTTPException(
                502,
                "Local model returned incomplete or invalid structured evidence citations; retry with a shorter question.",
            ) from exc
    cited = set(re.findall(r"\[((?:transaction|case|entity):[^\]]+)\]", content))
    return content, {
        "status": "unverified_text",
        "cited_ids": sorted(cited & known),
        "warning": "Model returned free text; citation structure is unverified.",
    }
