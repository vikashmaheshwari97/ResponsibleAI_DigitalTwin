from __future__ import annotations

from typing import Optional
from uuid import uuid4

from models.workflow_models import (
    FindingAnalysis,
    RemediationPlan,
    TwinComponentName,
)

try:
    from ollama import Client
except ImportError:
    Client = None


OLLAMA_HOST = "http://127.0.0.1:11434"

# A local CPU-backed Ollama call should not be able to leave the UI in a
# permanent "Running" state. The official Python client forwards timeout
# to its underlying HTTP client.
OLLAMA_TIMEOUT_SECONDS = 90.0


def _client():
    if Client is None:
        raise RuntimeError("The 'ollama' Python package is not installed.")

    return Client(
        host=OLLAMA_HOST,
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )


def get_available_models() -> dict:
    try:
        response = _client().list()

        raw_models = (
            response.get("models", [])
            if isinstance(response, dict)
            else getattr(response, "models", [])
        )

        names = []

        for item in raw_models:
            if isinstance(item, dict):
                name = item.get("model") or item.get("name")
            else:
                name = (
                    getattr(item, "model", None)
                    or getattr(item, "name", None)
                )

            if name:
                names.append(name)

        return {
            "connected": True,
            "models": sorted(set(names)),
            "error": None,
        }

    except Exception as exc:
        return {
            "connected": False,
            "models": [],
            "error": str(exc),
        }


def choose_preferred_model(
    models: list[str],
) -> Optional[str]:
    if not models:
        return None

    priorities = (
        "llama3",
        "llama",
        "qwen",
        "gemma",
        "mistral",
    )

    for keyword in priorities:
        for model in models:
            if keyword in model.lower():
                return model

    return models[0]


def _message_content(response) -> str:
    message = getattr(
        response,
        "message",
        None,
    )

    if message is not None:
        content = getattr(
            message,
            "content",
            None,
        )

        if content:
            return content

    if isinstance(response, dict):
        return (
            response
            .get("message", {})
            .get("content", "")
        )

    return str(response)


def analyse_security_finding(
    model: str,
    evidence: str,
) -> FindingAnalysis:

    response = _client().chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Security Analyst Agent inside a Responsible AI "
                    "Digital Twin laboratory. Analyse only the supplied local "
                    "synthetic sandbox evidence. For authenticated access to an "
                    "object owned by another user, classify it as "
                    "'Broken Object-Level Authorization'. The affected component "
                    "must be one of the schema values and for this scenario must "
                    "be 'Message API'. Confidence is categorical "
                    "(low/medium/high), not a probability. Be concise."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return the security assessment using the required JSON "
                    "schema. Evidence follows:\n\n"
                    + evidence
                ),
            },
        ],
        format=FindingAnalysis.model_json_schema(),
        options={
            "temperature": 0,
            # Keep output small and predictable for a local CPU demo.
            "num_predict": 220,
        },
    )

    analysis = FindingAnalysis.model_validate_json(
        _message_content(response)
    )

    if (
        analysis.classification
        == "Broken Object-Level Authorization"
    ):
        analysis.affected_component = (
            TwinComponentName.message_api
        )

    return analysis


def propose_remediation(
    model: str,
    finding: FindingAnalysis,
    evidence: str,
) -> RemediationPlan:

    response = _client().chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Remediation Agent inside a Responsible AI "
                    "Digital Twin laboratory. Recommend only defensive changes "
                    "to the local synthetic sandbox. For this authorization "
                    "finding target the 'Message API'. The proposal must remain "
                    "inside the Digital Twin sandbox and require human approval. "
                    "Be concise."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Generate the remediation using the required JSON schema.\n\n"
                    f"Structured finding:\n"
                    f"{finding.model_dump_json(indent=2)}\n\n"
                    f"Evidence:\n{evidence}"
                ),
            },
        ],
        format=RemediationPlan.model_json_schema(),
        options={
            "temperature": 0,
            "num_predict": 260,
        },
    )

    remediation = RemediationPlan.model_validate_json(
        _message_content(response)
    )

    remediation.remediation_id = (
        f"REM-{uuid4().hex[:10].upper()}"
    )

    remediation.target_component = (
        TwinComponentName.message_api
    )

    remediation.requires_human_approval = True

    remediation.target_environment = (
        "Digital Twin sandbox only"
    )

    return remediation
