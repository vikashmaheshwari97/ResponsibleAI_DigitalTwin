from __future__ import annotations

import hashlib
import json
from datetime import timezone

from sqlalchemy import select

from models.database_models import AuditEventRecord, TwinSnapshotRecord
from services.database_service import get_database_session

INTEGRITY_VERSION = "sha256-v1"


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def hash_payload(payload: dict) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _audit_hash_payload(event: AuditEventRecord, sequence_number: int, previous_hash: str | None) -> dict:
    created_at = event.created_at
    if created_at is not None:
        created_at = created_at.astimezone(timezone.utc).isoformat()
    return {
        "id": event.id,
        "run_id": event.run_id,
        "sequence_number": sequence_number,
        "previous_hash": previous_hash,
        "actor": event.actor,
        "category": event.category,
        "action": event.action,
        "status": event.status,
        "details": event.details,
        "created_at": created_at,
        "integrity_version": INTEGRITY_VERSION,
    }


def apply_hash_chain_to_run(run_id: str) -> dict:
    with get_database_session() as db:
        stmt = (
            select(AuditEventRecord)
            .where(AuditEventRecord.run_id == run_id)
            .order_by(AuditEventRecord.created_at.asc(), AuditEventRecord.id.asc())
        )
        events = list(db.scalars(stmt).all())
        previous_hash = None
        for index, event in enumerate(events, start=1):
            payload = _audit_hash_payload(event, index, previous_hash)
            event.sequence_number = index
            event.previous_hash = previous_hash
            event.integrity_version = INTEGRITY_VERSION
            event.event_hash = hash_payload(payload)
            previous_hash = event.event_hash
        db.commit()
        return {
            "run_id": run_id,
            "events": len(events),
            "last_hash": previous_hash,
            "integrity_version": INTEGRITY_VERSION,
        }


def verify_hash_chain(run_id: str) -> dict:
    with get_database_session() as db:
        stmt = (
            select(AuditEventRecord)
            .where(AuditEventRecord.run_id == run_id)
            .order_by(AuditEventRecord.sequence_number.asc().nullslast(), AuditEventRecord.created_at.asc())
        )
        events = list(db.scalars(stmt).all())
        if not events:
            return {"valid": True, "events": 0, "hashed_events": 0, "first_invalid_event": None}

        previous_hash = None
        hashed_events = 0
        for expected_sequence, event in enumerate(events, start=1):
            if event.event_hash is None:
                return {
                    "valid": False,
                    "events": len(events),
                    "hashed_events": hashed_events,
                    "first_invalid_event": event.id,
                    "reason": "Unhashed audit event detected.",
                }
            payload = _audit_hash_payload(event, expected_sequence, previous_hash)
            expected_hash = hash_payload(payload)
            if (
                event.sequence_number != expected_sequence
                or event.previous_hash != previous_hash
                or event.event_hash != expected_hash
                or event.integrity_version != INTEGRITY_VERSION
            ):
                return {
                    "valid": False,
                    "events": len(events),
                    "hashed_events": hashed_events,
                    "first_invalid_event": event.id,
                    "reason": "Hash-chain verification failed.",
                }
            hashed_events += 1
            previous_hash = event.event_hash

        return {
            "valid": True,
            "events": len(events),
            "hashed_events": hashed_events,
            "first_invalid_event": None,
            "last_hash": previous_hash,
        }


def snapshot_twin(run_id: str, twin: dict, phase: str, trigger: str) -> str:
    state_json = json.loads(json.dumps(twin, default=str))
    state_hash = hash_payload({"run_id": run_id, "phase": phase, "trigger": trigger, "state": state_json})
    record = TwinSnapshotRecord(
        run_id=run_id,
        twin_version=str(twin.get("version", "unknown")),
        phase=phase,
        trigger=trigger,
        state_json=state_json,
        state_hash=state_hash,
    )
    with get_database_session() as db:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.snapshot_id
