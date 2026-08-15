from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESTORE_MARKER = PROJECT_ROOT / "backups" / "restore_validation.json"


def _restore_validation() -> dict | None:
    if not RESTORE_MARKER.exists():
        return None
    try:
        payload = json.loads(RESTORE_MARKER.read_text(encoding="utf-8"))
    except Exception:
        return None
    if payload.get("status") != "PASS":
        return None
    return payload


def local_phase_status() -> list[dict]:
    restore = _restore_validation()
    phase_10_complete = restore is not None

    return [
        {
            "Phase": 1,
            "Area": "Streamlit visual PoC",
            "Progress": "100%",
            "State": "Complete",
        },
        {
            "Phase": 2,
            "Area": "Professional Digital Twin UI",
            "Progress": "100%",
            "State": "Research-console UI complete",
        },
        {
            "Phase": 3,
            "Area": "Real Digital Twin data model",
            "Progress": "100%",
            "State": "Core model frozen + contract tests",
        },
        {
            "Phase": 4,
            "Area": "Real local LLM agents",
            "Progress": "100%",
            "State": "Schema/fallback contract coverage complete",
        },
        {
            "Phase": 5,
            "Area": "Agent orchestration",
            "Progress": "100%",
            "State": "Lifecycle contract + terminal-state coverage",
        },
        {
            "Phase": 6,
            "Area": "Docker sandbox",
            "Progress": "100%",
            "State": "Complete",
        },
        {
            "Phase": 7,
            "Area": "SecureMessenger synthetic mini-app",
            "Progress": "100%",
            "State": "Complete",
        },
        {
            "Phase": 8,
            "Area": "Real controlled security testing",
            "Progress": "100%",
            "State": "4 approved scenarios",
        },
        {
            "Phase": 9,
            "Area": "Compliance / policy engine",
            "Progress": "100%",
            "State": "Policy/RBAC decision contracts covered",
        },
        {
            "Phase": 10,
            "Area": "PostgreSQL + audit/evidence/analytics/reports",
            "Progress": "100%" if phase_10_complete else "99%",
            "State": (
                "Complete · backup + isolated restore validated"
                if phase_10_complete
                else "Run isolated restore validation to close final 1%"
            ),
        },
        {
            "Phase": 11,
            "Area": "University of Tartu server deployment",
            "Progress": "0%",
            "State": "Deferred",
        },
    ]


def completion_summary() -> dict:
    rows = local_phase_status()
    completed = sum(
        1
        for row in rows
        if row["Phase"] <= 10 and str(row["Progress"]).replace("~", "") == "100%"
    )
    restore = _restore_validation()
    return {
        "local_phases_complete": completed,
        "local_phases_total": 10,
        "all_local_phases_complete": completed == 10,
        "restore_validation": restore,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase_status": rows,
    }
