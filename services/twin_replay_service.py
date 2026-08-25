from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from typing import Any

from models.twin_models import create_default_twin
from services.repository_service import (
    get_run_record,
    list_agent_events,
    list_security_tests,
    list_twin_snapshots,
)
from services.scenario_registry_service import get_scenario


OPERATIONS = [
    {
        "id": "O1",
        "name": "Plan",
        "subtitle": "Govern & prepare",
        "description": "Policy gate and Scenario Planner prepare the controlled experiment.",
    },
    {
        "id": "O2",
        "name": "Detect",
        "subtitle": "Test & analyse",
        "description": "Security Tester, Observer and Analyst identify unsafe behaviour and evidence.",
    },
    {
        "id": "O3",
        "name": "Remediate",
        "subtitle": "Propose & approve",
        "description": "The Remediation Agent proposes a defensive change under explicit human oversight.",
    },
    {
        "id": "O4",
        "name": "Verify",
        "subtitle": "Re-test & secure",
        "description": "Verification re-runs the scenario and records the secured Digital Twin state.",
    },
]

_COMPONENT_NAME_TO_ID = {
    "API Gateway": "gateway",
    "Authentication Service": "auth",
    "Message API": "message",
    "Message Database": "database",
    "Data Export Service": "data_export",
    "Integration Service": "integration",
    "Legal Request Service": "legal",
    "Bot Management Service": "bot_mgmt",
    "Feature Service": "feature",
}

_TRIGGER_PROGRESS: dict[str, tuple[int, int | None]] = {
    "run_started": (0, 1),
    "planning_complete": (1, 2),
    "security_test_complete": (1, 2),
    "observation_complete": (1, 2),
    "post_analysis": (2, None),
    "validation_complete_no_finding": (4, None),
    "remediation_proposed": (2, 3),
    "human_approved": (3, None),
    "verification_started": (3, 4),
    "secured": (4, None),
    "verification_complete": (4, None),
}

_TRIGGER_TITLES = {
    "run_started": "O1 · Governed run started",
    "planning_complete": "O1 complete · Controlled plan prepared",
    "security_test_complete": "O2 · Real sandbox test completed",
    "observation_complete": "O2 · Evidence observed",
    "post_analysis": "O2 complete · Finding analysed",
    "validation_complete_no_finding": "Secure expectation already satisfied",
    "remediation_proposed": "O3 · Defensive remediation proposed",
    "human_approved": "O3 complete · Human approval recorded",
    "verification_started": "O4 · Verification in progress",
    "secured": "O4 complete · Twin secured",
    "verification_complete": "O4 complete · Verification evidence finalised",
}

_TRIGGER_MESSAGES = {
    "run_started": "Policy-permitted experiment entered the controlled execution boundary.",
    "planning_complete": "The Scenario Planner completed the approved local test plan.",
    "security_test_complete": "A real localhost HTTP contract was executed against SecureMessenger.",
    "observation_complete": "The Observer evaluated the returned behaviour against the secure expectation.",
    "post_analysis": "The affected Twin component is marked vulnerable and structured analysis is persisted.",
    "validation_complete_no_finding": "The system already behaved securely; no remediation was required.",
    "remediation_proposed": "A sandbox-only defensive change is ready for explicit human review.",
    "human_approved": "A human reviewer authorised the defensive sandbox change.",
    "verification_started": "The secure profile is being applied and the same scenario is being re-tested.",
    "secured": "The affected Twin component passed verification and is marked secured.",
    "verification_complete": "Verification, policy and integrity evidence have been finalised.",
}

_TRIGGER_HOLD_MS = {
    "run_started": 2200,
    "planning_complete": 2200,
    "security_test_complete": 2400,
    "observation_complete": 2200,
    "post_analysis": 3400,
    "validation_complete_no_finding": 3600,
    "remediation_proposed": 3400,
    "human_approved": 2600,
    "verification_started": 2600,
    "secured": 3600,
    "verification_complete": 3600,
}


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _operation_states(completed_through: int, active: int | None) -> list[dict]:
    output: list[dict] = []
    for index, operation in enumerate(OPERATIONS, start=1):
        if index <= completed_through:
            status = "complete"
        elif active == index:
            status = "active"
        else:
            status = "pending"
        output.append({**operation, "status": status})
    return output


def _progress_from_phase(phase: str) -> tuple[int, int | None]:
    phase = (phase or "ready").lower()
    if phase == "running":
        return (0, 1)
    if phase == "vulnerable":
        return (2, None)
    if phase in {"awaiting_approval", "remediating"}:
        return (2, 3)
    if phase == "verifying":
        return (3, 4)
    if phase in {"secured", "validated"}:
        return (4, None)
    if phase in {"failed", "rejected", "interrupted", "aborted"}:
        return (0, None)
    return (0, None)


def operation_states(phase: str, trigger: str | None = None) -> list[dict]:
    completed, active = _TRIGGER_PROGRESS.get(trigger or "", _progress_from_phase(phase))
    return _operation_states(completed, active)


def _focus_operation(operations: list[dict]) -> str:
    for item in operations:
        if item["status"] == "active":
            return item["id"]
    completed = [item for item in operations if item["status"] == "complete"]
    return completed[-1]["id"] if completed else "O1"


def _active_component_id(twin: dict, preferred: str | None = None) -> str | None:
    components = twin.get("components", {})
    if preferred and preferred in components:
        return preferred
    for status in ("vulnerable", "testing", "secured"):
        for component_id, component in components.items():
            if component.get("status") == status:
                return component_id
    return None


def _scenario_component_id(scenario_id: str | None) -> str | None:
    if not scenario_id:
        return None
    try:
        scenario = get_scenario(scenario_id)
    except Exception:
        return None
    return _COMPONENT_NAME_TO_ID.get(scenario.affected_component.value)


def build_live_frame(
    twin: dict,
    phase: str,
    *,
    scenario_id: str | None = None,
    message: str | None = None,
) -> dict:
    operations = operation_states(phase)
    preferred = _scenario_component_id(scenario_id)
    return {
        "frame_id": "LIVE",
        "index": 0,
        "phase": phase,
        "trigger": "live_state",
        "title": f"Live Twin · {phase.replace('_', ' ').title()}",
        "message": message or "Current state from the governed Digital Twin session.",
        "created_at": None,
        "state_hash": None,
        "hold_ms": 2500,
        "focus_operation": _focus_operation(operations),
        "operations": operations,
        "active_component": _active_component_id(twin, preferred),
        "twin": deepcopy(twin),
        "evidence": [],
    }


def _events_for_window(events: list, start: datetime | None, end: datetime | None) -> list[str]:
    selected: list[str] = []
    for event in events:
        created = getattr(event, "created_at", None)
        if created is None:
            continue
        if start is not None and created <= start:
            continue
        if end is not None and created > end:
            continue
        selected.append(f"{event.agent}: {event.action}")
    return selected[-4:]


def _test_evidence_for_trigger(tests: list, trigger: str) -> list[str]:
    if not tests:
        return []
    if trigger in {"security_test_complete", "observation_complete", "post_analysis"}:
        candidates = [item for item in tests if getattr(item, "stage", "") == "initial"]
    elif trigger in {"verification_started", "secured", "verification_complete"}:
        candidates = [item for item in tests if getattr(item, "stage", "") == "verification"]
    else:
        candidates = []
    if not candidates:
        return []
    item = candidates[-1]
    return [
        (
            f"HTTP evidence: expected {item.expected_status}, observed {item.observed_status}, "
            f"result {item.result}."
        )
    ]


def build_persisted_replay(run_id: str) -> dict:
    run = get_run_record(run_id)
    if run is None:
        raise ValueError(f"Unknown run_id: {run_id}")

    snapshots = list_twin_snapshots(run_id)
    events = list_agent_events(run_id)
    tests = list_security_tests(run_id)
    preferred_component = _scenario_component_id(run.scenario_id)

    frames: list[dict] = []
    previous_time: datetime | None = None
    for index, snapshot in enumerate(snapshots):
        trigger = snapshot.trigger or "snapshot"
        operations = operation_states(snapshot.phase, trigger)
        evidence = _events_for_window(events, previous_time, snapshot.created_at)
        evidence.extend(_test_evidence_for_trigger(tests, trigger))
        frame = {
            "frame_id": snapshot.snapshot_id,
            "index": index,
            "phase": snapshot.phase,
            "trigger": trigger,
            "title": _TRIGGER_TITLES.get(
                trigger,
                f"Twin snapshot · {str(trigger).replace('_', ' ').title()}",
            ),
            "message": evidence[-1] if evidence else _TRIGGER_MESSAGES.get(
                trigger,
                "Evidence-backed Digital Twin state captured during the governed run.",
            ),
            "created_at": _iso(snapshot.created_at),
            "state_hash": snapshot.state_hash,
            "hold_ms": _TRIGGER_HOLD_MS.get(trigger, 2400),
            "focus_operation": _focus_operation(operations),
            "operations": operations,
            "active_component": _active_component_id(snapshot.state_json, preferred_component),
            "twin": deepcopy(snapshot.state_json),
            "evidence": evidence,
        }
        frames.append(frame)
        previous_time = snapshot.created_at

    if frames and events:
        tail = _events_for_window(events, previous_time, None)
        if tail:
            frames[-1]["evidence"].extend(tail)
            frames[-1]["message"] = tail[-1]

    return {
        "schema_version": "rai-twin-replay-v1",
        "source": "postgresql-twin-snapshots",
        "run": {
            "run_id": run.run_id,
            "scenario_id": run.scenario_id,
            "scenario_name": run.scenario_name,
            "status": run.status,
            "result": run.result,
            "started_at": _iso(run.started_at),
            "completed_at": _iso(run.completed_at),
            "initial_twin_version": run.initial_twin_version,
            "final_twin_version": run.final_twin_version,
        },
        "frames": frames,
    }


def _set_component_status(twin: dict, component_id: str, status: str, version: str | None = None) -> dict:
    output = deepcopy(twin)
    if component_id in output.get("components", {}):
        output["components"][component_id]["status"] = status
        if version:
            output["components"][component_id]["version"] = version
    if version:
        output["version"] = version
    return output


def build_demo_replay() -> dict:
    base = create_default_twin()
    component_id = "message"
    frames_spec = [
        (
            "DEMO-01",
            "running",
            "run_started",
            _set_component_status(base, component_id, "testing"),
            "Policy gate passed. The Scenario Planner starts the controlled authorization experiment.",
        ),
        (
            "DEMO-02",
            "running",
            "security_test_complete",
            _set_component_status(base, component_id, "testing"),
            "Alice requests Bob's synthetic MSG-204. The vulnerable sandbox returns HTTP 200.",
        ),
        (
            "DEMO-03",
            "vulnerable",
            "post_analysis",
            _set_component_status(base, component_id, "vulnerable"),
            "The Message API is marked vulnerable after the structured finding is persisted.",
        ),
        (
            "DEMO-04",
            "awaiting_approval",
            "remediation_proposed",
            _set_component_status(base, component_id, "vulnerable"),
            "A defensive authorization change is proposed and waits for explicit human approval.",
        ),
        (
            "DEMO-05",
            "verifying",
            "verification_started",
            _set_component_status(base, component_id, "testing", "1.1"),
            "The approved secure profile is applied and the same authorization request is re-tested.",
        ),
        (
            "DEMO-06",
            "secured",
            "secured",
            _set_component_status(base, component_id, "secured", "1.1"),
            "Verification returns the expected HTTP 403. The Message API is marked secured.",
        ),
    ]

    frames: list[dict] = []
    for index, (frame_id, phase, trigger, twin, message) in enumerate(frames_spec):
        operations = operation_states(phase, trigger)
        frames.append(
            {
                "frame_id": frame_id,
                "index": index,
                "phase": phase,
                "trigger": trigger,
                "title": _TRIGGER_TITLES.get(trigger, trigger),
                "message": message,
                "created_at": None,
                "state_hash": None,
                "hold_ms": _TRIGGER_HOLD_MS.get(trigger, 2400),
                "focus_operation": _focus_operation(operations),
                "operations": operations,
                "active_component": component_id,
                "twin": twin,
                "evidence": [message],
            }
        )

    return {
        "schema_version": "rai-twin-replay-v1",
        "source": "built-in-demonstration",
        "run": {
            "run_id": "DEMO-SCN-001",
            "scenario_id": "SCN-001",
            "scenario_name": "Unauthorized Private Message Access",
            "status": "secured",
            "result": "PASS",
            "started_at": None,
            "completed_at": None,
            "initial_twin_version": "1.0",
            "final_twin_version": "1.1",
        },
        "frames": frames,
    }


def replay_json(bundle: dict) -> str:
    return json.dumps(bundle, indent=2, ensure_ascii=False, default=str)
