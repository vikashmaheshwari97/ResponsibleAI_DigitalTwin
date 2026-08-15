from models.workflow_models import PolicyOutcome
from services import policy_service


def _healthy_database():
    return {"connected": True, "database": "rai_twin", "url": "test", "error": None}


def test_validation_policy_permits_approved_local_scenario(monkeypatch):
    monkeypatch.setattr(policy_service, "database_health", _healthy_database)
    monkeypatch.setattr(policy_service, "can_execute_scenarios", lambda: True)

    decision = policy_service.evaluate_validation_policy("SCN-001")

    assert decision.outcome == PolicyOutcome.permit


def test_remediation_waits_for_human_approval(monkeypatch):
    monkeypatch.setattr(policy_service, "database_health", _healthy_database)
    monkeypatch.setattr(policy_service, "can_execute_scenarios", lambda: True)

    pending = policy_service.evaluate_remediation_policy("SCN-001", human_approved=False)
    approved = policy_service.evaluate_remediation_policy("SCN-001", human_approved=True)

    assert pending.outcome == PolicyOutcome.permit_with_approval
    assert approved.outcome == PolicyOutcome.permit


def test_external_environment_is_blocked(monkeypatch):
    monkeypatch.setattr(policy_service, "database_health", _healthy_database)
    monkeypatch.setattr(policy_service, "can_execute_scenarios", lambda: True)

    decision, _ = policy_service.evaluate_action(
        action="Unsafe external action",
        target="SecureMessenger",
        environment="external production",
        scenario_id="SCN-001",
        requires_human_approval=False,
    )

    assert decision.outcome == PolicyOutcome.block


def test_unauthorized_actor_is_blocked(monkeypatch):
    monkeypatch.setattr(policy_service, "database_health", _healthy_database)
    monkeypatch.setattr(policy_service, "can_execute_scenarios", lambda: False)

    decision = policy_service.evaluate_validation_policy("SCN-001")

    assert decision.outcome == PolicyOutcome.block
