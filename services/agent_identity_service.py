from __future__ import annotations

from dataclasses import asdict, dataclass


PROTOTYPE_IDENTITY_SCHEME = "Estonian e-Identity concept · research prototype"
PROTOTYPE_IDENTITY_NOTE = (
    "The e-Identity values shown in this research prototype are synthetic hardcoded identifiers "
    "for AI-agent traceability. They are not credentials actually issued by the Estonian Government."
)


@dataclass(frozen=True)
class AgentIdentity:
    name: str
    e_identity_id: str
    role: str
    operation: str
    description: str

    def to_dict(self, *, status: str | None = None) -> dict:
        payload = asdict(self)
        if status is not None:
            payload["status"] = status
        return payload


_AGENT_IDENTITIES: tuple[AgentIdentity, ...] = (
    AgentIdentity(
        "Scenario Planner",
        "EE-AI-PROT-2026-001",
        "Governed experiment planner",
        "O1 · Plan",
        "Transforms an approved scenario into the controlled validation plan.",
    ),
    AgentIdentity(
        "Security Testing Agent",
        "EE-AI-PROT-2026-002",
        "Controlled security tester",
        "O2 · Detect",
        "Executes the approved localhost HTTP validation against SecureMessenger.",
    ),
    AgentIdentity(
        "Observer Agent",
        "EE-AI-PROT-2026-003",
        "Evidence observer",
        "O2 · Detect",
        "Compares observed sandbox behaviour with the expected secure contract.",
    ),
    AgentIdentity(
        "Security Analyst",
        "EE-AI-PROT-2026-004",
        "Responsible-AI security analyst",
        "O2 · Detect",
        "Produces schema-validated analysis using the local LLM or deterministic fallback.",
    ),
    AgentIdentity(
        "Remediation Agent",
        "EE-AI-PROT-2026-005",
        "Defensive remediation proposer",
        "O3 · Remediate",
        "Proposes sandbox-only defensive remediation under explicit human oversight.",
    ),
    AgentIdentity(
        "Verification Agent",
        "EE-AI-PROT-2026-006",
        "Post-remediation verifier",
        "O4 · Verify",
        "Re-runs the controlled scenario and confirms the secured Digital Twin state.",
    ),
)

_BY_NAME = {item.name: item for item in _AGENT_IDENTITIES}


def list_agent_identities(statuses: dict[str, str] | None = None) -> list[dict]:
    statuses = statuses or {}
    return [
        identity.to_dict(status=statuses.get(identity.name, "Ready"))
        for identity in _AGENT_IDENTITIES
    ]


def get_agent_identity(name: str) -> AgentIdentity | None:
    return _BY_NAME.get(name)


def agent_identity_id(name: str) -> str | None:
    identity = get_agent_identity(name)
    return identity.e_identity_id if identity else None
