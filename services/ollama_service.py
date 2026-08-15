from __future__ import annotations

from typing import Optional
from uuid import uuid4

from models.workflow_models import FindingAnalysis, RemediationPlan
from services.config_service import get_setting
from services.scenario_registry_service import ScenarioDefinition

try:
    from ollama import Client
except ImportError:
    Client = None


OLLAMA_HOST = get_setting("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_TIMEOUT_SECONDS = 90.0


def _client():
    if Client is None:
        raise RuntimeError("The 'ollama' Python package is not installed.")
    return Client(host=OLLAMA_HOST, timeout=OLLAMA_TIMEOUT_SECONDS)


def get_available_models() -> dict:
    try:
        response = _client().list()
        raw_models = (
            response.get("models", [])
            if isinstance(response, dict)
            else getattr(response, "models", [])
        )
        names: list[str] = []
        for item in raw_models:
            if isinstance(item, dict):
                name = item.get("model") or item.get("name")
            else:
                name = getattr(item, "model", None) or getattr(item, "name", None)
            if name:
                names.append(name)
        return {"connected": True, "models": sorted(set(names)), "error": None}
    except Exception as exc:
        return {"connected": False, "models": [], "error": str(exc)}


def choose_preferred_model(models: list[str]) -> Optional[str]:
    if not models:
        return None
    for keyword in ("llama3", "llama", "qwen", "gemma", "mistral"):
        for model in models:
            if keyword in model.lower():
                return model
    return models[0]


def _message_content(response) -> str:
    message = getattr(response, "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if content:
            return content
    if isinstance(response, dict):
        return response.get("message", {}).get("content", "")
    return str(response)


def analyse_security_finding(
    model: str,
    evidence: str,
    scenario: ScenarioDefinition,
) -> FindingAnalysis:
    response = _client().chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Security Analyst Agent inside a Responsible AI "
                    "Digital Twin laboratory. Analyse only the supplied local, "
                    "synthetic sandbox evidence. Return concise schema-valid data. "
                    f"The approved scenario is {scenario.scenario_id}: {scenario.name}. "
                    f"Expected classification: {scenario.classification}. "
                    f"Affected component must be '{scenario.affected_component.value}'. "
                    "Confidence is categorical (low/medium/high), not a probability. "
                    "Do not propose offensive actions or external targets."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return the security assessment using the required JSON schema.\n\n"
                    + evidence
                ),
            },
        ],
        format=FindingAnalysis.model_json_schema(),
        options={"temperature": 0, "num_predict": 260},
    )

    analysis = FindingAnalysis.model_validate_json(_message_content(response))
    # The scenario registry is the control-plane source of truth for the target.
    analysis.affected_component = scenario.affected_component
    if not analysis.classification.strip():
        analysis.classification = scenario.classification
    return analysis


def propose_remediation(
    model: str,
    finding: FindingAnalysis,
    evidence: str,
    scenario: ScenarioDefinition,
) -> RemediationPlan:
    response = _client().chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Remediation Agent inside a Responsible AI Digital "
                    "Twin laboratory. Recommend only defensive changes to the local "
                    "synthetic sandbox. The approved target component is "
                    f"'{scenario.affected_component.value}'. The proposal must remain "
                    "inside the Digital Twin sandbox and must require human approval. "
                    "Do not provide instructions for external systems."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Generate the remediation using the required JSON schema.\n\n"
                    f"Approved scenario: {scenario.name}\n"
                    f"Registry remediation goal: {scenario.remediation_change}\n\n"
                    f"Structured finding:\n{finding.model_dump_json(indent=2)}\n\n"
                    f"Evidence:\n{evidence}"
                ),
            },
        ],
        format=RemediationPlan.model_json_schema(),
        options={"temperature": 0, "num_predict": 320},
    )

    remediation = RemediationPlan.model_validate_json(_message_content(response))
    remediation.remediation_id = f"REM-{uuid4().hex[:10].upper()}"
    remediation.target_component = scenario.affected_component
    remediation.requires_human_approval = True
    remediation.target_environment = "Digital Twin sandbox only"
    return remediation
