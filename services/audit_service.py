from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from services.evidence_service import (
    apply_hash_chain_to_run,
)
from services.repository_service import (
    list_audit_events as list_persistent_audit_events,
    save_audit_event,
)


def _current_run_id() -> str | None:
    raw = st.session_state.get(
        "current_run"
    )

    if isinstance(raw, dict):
        return raw.get(
            "run_id"
        )

    return None


def add_audit_event(
    actor: str,
    action: str,
    status: str = "Success",
    category: str = "System",
    details: str = "",
) -> dict:

    event = {
        "Time": (
            datetime.now(timezone.utc)
            .astimezone()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ),
        "Actor": actor,
        "Category": category,
        "Action": action,
        "Status": status,
        "Details": details,
    }

    st.session_state.audit_log.append(
        event
    )

    run_id = _current_run_id()

    save_audit_event(
        run_id=run_id,
        actor=actor,
        category=category,
        action=action,
        status=status,
        details=details,
    )

    # Keep even incomplete runs tamper-evident. For this small PoC,
    # rebuilding the current run's short chain on each event is simple,
    # deterministic, and makes interrupted runs verifiable.
    if run_id:
        apply_hash_chain_to_run(
            run_id
        )

    return event


def get_audit_events() -> list[dict]:
    return list(
        st.session_state.get(
            "audit_log",
            [],
        )
    )


def get_persistent_audit_events(
    run_id: str | None = None,
) -> list[dict]:

    records = (
        list_persistent_audit_events(
            run_id=run_id
        )
    )

    return [
        {
            "Time": (
                record.created_at
                .astimezone()
                .strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ),
            "Run ID": record.run_id,
            "Actor": record.actor,
            "Category": record.category,
            "Action": record.action,
            "Status": record.status,
            "Details": record.details,
            "Sequence": record.sequence_number,
            "Hash": record.event_hash,
        }
        for record in records
    ]
