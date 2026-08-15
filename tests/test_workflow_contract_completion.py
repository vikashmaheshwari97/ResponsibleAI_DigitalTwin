from services.workflow_contract_service import (
    happy_path_already_secure,
    happy_path_with_remediation,
    is_valid_transition,
    validate_path,
)


def test_remediation_happy_path_is_valid():
    valid, reason = validate_path(happy_path_with_remediation())
    assert valid is True
    assert reason is None


def test_already_secure_happy_path_is_valid():
    valid, reason = validate_path(happy_path_already_secure())
    assert valid is True
    assert reason is None


def test_invalid_skip_is_rejected():
    assert is_valid_transition("ready", "secured") is False
    valid, reason = validate_path(["ready", "running", "secured"])
    assert valid is False
    assert "running -> secured" in reason


def test_terminal_states_do_not_transition():
    for terminal in ("secured", "validated", "failed", "rejected", "interrupted", "aborted"):
        assert is_valid_transition(terminal, "running") is False
