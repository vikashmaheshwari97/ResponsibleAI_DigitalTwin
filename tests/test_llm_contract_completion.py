import json

from models.workflow_models import FindingAnalysis
from services import ollama_service
from services.scenario_registry_service import get_scenario


class _Message:
    def __init__(self, content: str):
        self.content = content


class _Response:
    def __init__(self, content: str):
        self.message = _Message(content)


class _FakeClient:
    def __init__(self, payload: dict):
        self.payload = payload

    def chat(self, **_kwargs):
        return _Response(json.dumps(self.payload))


def test_preferred_model_selection_is_deterministic():
    models = ["mistral:latest", "qwen3:8b", "llama3.2:3b"]
    assert ollama_service.choose_preferred_model(models) == "llama3.2:3b"
    assert ollama_service.choose_preferred_model([]) is None


def test_security_analysis_is_schema_valid_and_target_locked(monkeypatch):
    scenario = get_scenario("SCN-001")
    payload = {
        "classification": "Broken Object-Level Authorization",
        "severity": "high",
        "confidence": "high",
        "affected_component": "API Gateway",
        "root_cause": "Ownership was not enforced.",
        "security_impact": "Synthetic cross-user message access.",
        "recommended_action": "Enforce ownership checks.",
    }

    monkeypatch.setattr(
        ollama_service,
        "_client",
        lambda: _FakeClient(payload),
    )

    result = ollama_service.analyse_security_finding(
        model="llama3.2:3b",
        evidence="Expected 403, observed 200.",
        scenario=scenario,
    )

    assert isinstance(result, FindingAnalysis)
    assert result.affected_component == scenario.affected_component
    assert result.classification


def test_remediation_is_forced_to_human_governed_sandbox(monkeypatch):
    scenario = get_scenario("SCN-001")
    finding = FindingAnalysis(
        classification=scenario.classification,
        severity=scenario.severity,
        confidence=scenario.confidence,
        affected_component=scenario.affected_component,
        root_cause=scenario.root_cause,
        security_impact=scenario.security_impact,
        recommended_action=scenario.recommended_action,
    )
    payload = {
        "remediation_id": "REM-FAKE",
        "title": "Enforce ownership checks",
        "target_component": "API Gateway",
        "action_type": "configuration",
        "proposed_change": "Validate synthetic message ownership.",
        "risk": "low",
        "expected_security_benefit": "Prevent cross-user access.",
        "possible_side_effects": ["Synthetic requests without ownership will be denied."],
        "verification_test": "Repeat the same controlled request.",
        "requires_human_approval": False,
        "target_environment": "external production",
    }

    monkeypatch.setattr(
        ollama_service,
        "_client",
        lambda: _FakeClient(payload),
    )

    result = ollama_service.propose_remediation(
        model="llama3.2:3b",
        finding=finding,
        evidence="Synthetic local evidence.",
        scenario=scenario,
    )

    assert result.target_component == scenario.affected_component
    assert result.requires_human_approval is True
    assert result.target_environment == "Digital Twin sandbox only"
    assert result.remediation_id.startswith("REM-")
