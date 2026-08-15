from __future__ import annotations

from dataclasses import asdict, dataclass

from models.workflow_models import Severity, TwinComponentName


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    name: str
    category: str
    objective: str
    description: str
    affected_component: TwinComponentName
    classification: str
    severity: Severity
    confidence: str
    root_cause: str
    security_impact: str
    recommended_action: str
    remediation_title: str
    remediation_action_type: str
    remediation_change: str
    remediation_benefit: str
    remediation_side_effects: tuple[str, ...]
    verification_test: str
    expected_status: int
    test_kind: str

    def public_dict(self) -> dict:
        payload = asdict(self)
        payload["affected_component"] = self.affected_component.value
        payload["severity"] = self.severity.value
        payload["remediation_side_effects"] = list(self.remediation_side_effects)
        return payload


SCENARIOS: dict[str, ScenarioDefinition] = {
    "SCN-001": ScenarioDefinition(
        scenario_id="SCN-001",
        name="Unauthorized Private Message Access",
        category="Authorization",
        objective=(
            "Validate whether Alice can retrieve Bob's synthetic MSG-204. "
            "Correct behavior is HTTP 403."
        ),
        description=(
            "Controlled object-level authorization validation against the local "
            "SecureMessenger Message API."
        ),
        affected_component=TwinComponentName.message_api,
        classification="Broken Object-Level Authorization",
        severity=Severity.high,
        confidence="high",
        root_cause=(
            "The Message API authenticates the requester but, in the vulnerable "
            "profile, does not verify that the authenticated user owns the "
            "requested private message."
        ),
        security_impact=(
            "A synthetic authenticated user can read another synthetic user's "
            "private message."
        ),
        recommended_action=(
            "Enforce resource ownership before returning a private message."
        ),
        remediation_title="Enforce object-level authorization",
        remediation_action_type="Authorization control",
        remediation_change=(
            "Verify that the authenticated synthetic user owns the requested "
            "message before returning the resource."
        ),
        remediation_benefit="Cross-user private-message disclosure is denied.",
        remediation_side_effects=(
            "Unauthorized cross-user requests return HTTP 403.",
            "Client tests must distinguish owned and non-owned resources.",
        ),
        verification_test=(
            "Repeat Alice → MSG-204 and require HTTP 403 while owned resources "
            "remain accessible."
        ),
        expected_status=403,
        test_kind="bola",
    ),
    "SCN-002": ScenarioDefinition(
        scenario_id="SCN-002",
        name="Expired Authentication Token Acceptance",
        category="Authentication",
        objective=(
            "Validate whether a deliberately expired synthetic Alice token is "
            "rejected. Correct behavior is HTTP 401."
        ),
        description=(
            "Controlled expired-token validation using a synthetic token that is "
            "never valid outside the local SecureMessenger sandbox."
        ),
        affected_component=TwinComponentName.authentication_service,
        classification="Improper Expired Token Validation",
        severity=Severity.high,
        confidence="high",
        root_cause=(
            "The vulnerable authentication profile recognizes a synthetic expired "
            "token without enforcing its expiry state."
        ),
        security_impact=(
            "A synthetic expired session can continue to access authenticated "
            "sandbox functionality."
        ),
        recommended_action="Reject expired access tokens before resolving the user identity.",
        remediation_title="Enforce synthetic token expiry",
        remediation_action_type="Authentication validation",
        remediation_change=(
            "Require active token state before authenticating a synthetic user and "
            "return HTTP 401 for the predefined expired token."
        ),
        remediation_benefit="Expired synthetic sessions are consistently rejected.",
        remediation_side_effects=(
            "Expired sessions must re-authenticate.",
            "Authentication tests now require explicit active/expired token cases.",
        ),
        verification_test=(
            "Repeat the expired-token request to /users/me and require HTTP 401."
        ),
        expected_status=401,
        test_kind="expired_token",
    ),
    "SCN-003": ScenarioDefinition(
        scenario_id="SCN-003",
        name="Malformed Synthetic Message Payload",
        category="Input Validation",
        objective=(
            "Submit a deliberately malformed synthetic message payload. Correct "
            "behavior is HTTP 422."
        ),
        description=(
            "Controlled request-validation scenario using only synthetic content "
            "and a local POST /messages endpoint."
        ),
        affected_component=TwinComponentName.message_api,
        classification="Insufficient Server-Side Input Validation",
        severity=Severity.medium,
        confidence="high",
        root_cause=(
            "The vulnerable Message API accepts an empty body, an out-of-range "
            "priority value, and an unexpected field without server-side checks."
        ),
        security_impact=(
            "Malformed synthetic data can enter the application workflow and reduce "
            "the reliability of downstream controls."
        ),
        recommended_action=(
            "Validate required fields, allowed keys, content length, recipient and "
            "priority constraints before accepting a message."
        ),
        remediation_title="Enforce message payload validation",
        remediation_action_type="Input validation",
        remediation_change=(
            "Reject malformed synthetic message payloads with HTTP 422 using "
            "explicit server-side validation."
        ),
        remediation_benefit="Malformed synthetic requests are rejected before processing.",
        remediation_side_effects=(
            "Previously tolerated malformed requests receive HTTP 422.",
            "Clients must send schema-compliant synthetic payloads.",
        ),
        verification_test=(
            "Repeat the same malformed POST /messages payload and require HTTP 422."
        ),
        expected_status=422,
        test_kind="malformed_payload",
    ),
    "SCN-004": ScenarioDefinition(
        scenario_id="SCN-004",
        name="Local Request Burst Without Rate Control",
        category="Abuse Control",
        objective=(
            "Send a small deterministic burst of synthetic localhost requests. "
            "The final request should be rate-limited with HTTP 429."
        ),
        description=(
            "Controlled local-only abuse-control test. It sends eight requests to "
            "a dedicated sandbox endpoint and never targets an external system."
        ),
        affected_component=TwinComponentName.api_gateway,
        classification="Missing Local Rate Limiting",
        severity=Severity.medium,
        confidence="high",
        root_cause=(
            "The vulnerable gateway profile does not enforce the predefined small "
            "per-user request threshold on the dedicated synthetic rate-test endpoint."
        ),
        security_impact=(
            "A synthetic client can exceed the intended local request threshold "
            "without receiving a throttling response."
        ),
        recommended_action=(
            "Enforce the predefined local request threshold and return HTTP 429 once "
            "the synthetic burst exceeds it."
        ),
        remediation_title="Enable local abuse-control threshold",
        remediation_action_type="Rate limiting",
        remediation_change=(
            "Apply the sandbox's deterministic per-user request counter and return "
            "HTTP 429 after five requests in the controlled test window."
        ),
        remediation_benefit="Synthetic request bursts are throttled deterministically.",
        remediation_side_effects=(
            "Requests above the local test threshold receive HTTP 429.",
            "Verification resets the in-memory test counter before execution.",
        ),
        verification_test=(
            "Repeat the same eight-request localhost burst and require the final "
            "response to be HTTP 429."
        ),
        expected_status=429,
        test_kind="rate_limit",
    ),
}


def list_scenarios() -> list[ScenarioDefinition]:
    return [SCENARIOS[key] for key in sorted(SCENARIOS)]


def get_scenario(scenario_id: str) -> ScenarioDefinition:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        raise KeyError(f"Unknown approved scenario: {scenario_id}") from exc


def scenario_by_name(name: str) -> ScenarioDefinition:
    for scenario in SCENARIOS.values():
        if scenario.name == name:
            return scenario
    raise KeyError(f"Unknown approved scenario name: {name}")


def is_approved_scenario(scenario_id: str) -> bool:
    return scenario_id in SCENARIOS
