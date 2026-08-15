from __future__ import annotations


WORKFLOW_STAGES = (
    "ready",
    "running",
    "vulnerable",
    "awaiting_approval",
    "remediating",
    "verifying",
    "secured",
)

TERMINAL_STAGES = {
    "secured",
    "validated",
    "failed",
    "rejected",
    "interrupted",
    "aborted",
}

ALLOWED_TRANSITIONS = {
    "ready": {"running"},
    "running": {"vulnerable", "validated", "failed", "interrupted", "aborted"},
    "vulnerable": {"awaiting_approval", "failed", "interrupted", "aborted"},
    "awaiting_approval": {"vulnerable", "remediating", "rejected", "failed", "interrupted", "aborted"},
    "remediating": {"verifying", "failed", "interrupted", "aborted"},
    "verifying": {"secured", "failed", "interrupted", "aborted"},
    "secured": set(),
    "validated": set(),
    "failed": set(),
    "rejected": set(),
    "interrupted": set(),
    "aborted": set(),
}


def allowed_transitions(phase: str) -> set[str]:
    return set(ALLOWED_TRANSITIONS.get(phase, set()))


def is_valid_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def validate_path(phases: list[str] | tuple[str, ...]) -> tuple[bool, str | None]:
    if len(phases) < 2:
        return True, None
    for current, target in zip(phases, phases[1:]):
        if not is_valid_transition(current, target):
            return False, f"Invalid workflow transition: {current} -> {target}"
    return True, None


def happy_path_with_remediation() -> tuple[str, ...]:
    return (
        "ready",
        "running",
        "vulnerable",
        "awaiting_approval",
        "remediating",
        "verifying",
        "secured",
    )


def happy_path_already_secure() -> tuple[str, ...]:
    return ("ready", "running", "validated")
