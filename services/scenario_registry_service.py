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
    "SCN-005": ScenarioDefinition(
        scenario_id="SCN-005",
        name="Bulk User-Data Exfiltration",
        category="Data Protection",
        objective=(
            "Request an unlimited bulk export of all synthetic messages. "
            "Correct behavior is HTTP 429 when the bulk threshold is exceeded."
        ),
        description=(
            "Controlled bulk data exfiltration test. A compromised service "
            "attempts to retrieve all messages from the synthetic messaging "
            "platform in a single operation."
        ),
        affected_component=TwinComponentName.data_export_service,
        classification="Unrestricted Bulk Data Access",
        severity=Severity.critical,
        confidence="high",
        root_cause=(
            "The vulnerable Data Export Service does not enforce per-user bulk "
            "export limits, allowing unlimited retrieval of all synthetic messages."
        ),
        security_impact=(
            "A compromised or malicious service can exfiltrate the entire "
            "synthetic message store in a single request."
        ),
        recommended_action=(
            "Enforce a per-user bulk export threshold and return HTTP 429 "
            "when the limit is exceeded."
        ),
        remediation_title="Enforce bulk data export limits",
        remediation_action_type="Data access control",
        remediation_change=(
            "Apply a per-user counter on the bulk export endpoint and reject "
            "requests exceeding the predefined threshold with HTTP 429."
        ),
        remediation_benefit="Bulk data exfiltration attempts are throttled deterministically.",
        remediation_side_effects=(
            "Export requests exceeding the threshold receive HTTP 429.",
            "Legitimate bulk operations must be batched below the threshold.",
        ),
        verification_test=(
            "Repeat bulk export requests and verify the final response is HTTP 429."
        ),
        expected_status=429,
        test_kind="bulk_exfiltration",
    ),
    "SCN-006": ScenarioDefinition(
        scenario_id="SCN-006",
        name="Unauthorized Third-Party Data Sharing",
        category="Privacy",
        objective=(
            "Share synthetic user data with an unauthorized external marketing "
            "service. Correct behavior is HTTP 403."
        ),
        description=(
            "Controlled third-party data sharing test. The messaging platform "
            "attempts to send synthetic user data to an external service that "
            "has not been authorized for data access."
        ),
        affected_component=TwinComponentName.integration_service,
        classification="Unauthorized Data Sharing",
        severity=Severity.critical,
        confidence="high",
        root_cause=(
            "The vulnerable Integration Service does not verify whether a "
            "third-party recipient is authorized before sharing synthetic "
            "user data."
        ),
        security_impact=(
            "Synthetic user data can be shared with unauthorized external "
            "services without any access control check."
        ),
        recommended_action=(
            "Verify third-party authorization status before sharing any "
            "synthetic user data."
        ),
        remediation_title="Enforce third-party authorization check",
        remediation_action_type="Data sharing control",
        remediation_change=(
            "Check the integration's authorized status before sharing data "
            "and return HTTP 403 for unauthorized third-party recipients."
        ),
        remediation_benefit="Unauthorized third-party data sharing is blocked.",
        remediation_side_effects=(
            "Sharing requests to unauthorized integrations receive HTTP 403.",
            "New integrations must be explicitly authorized before data access.",
        ),
        verification_test=(
            "Repeat the share request to the unauthorized integration and "
            "require HTTP 403."
        ),
        expected_status=403,
        test_kind="unauthorized_sharing",
    ),
    "SCN-007": ScenarioDefinition(
        scenario_id="SCN-007",
        name="Government Data Request",
        category="Governance",
        objective=(
            "Submit a government data request without a valid legal basis. "
            "Correct behavior is HTTP 403."
        ),
        description=(
            "Controlled government data request scenario. A government entity "
            "requests access to synthetic user data, but the request lacks "
            "a valid legal basis or court order."
        ),
        affected_component=TwinComponentName.legal_request_service,
        classification="Government Request Without Legal Basis",
        severity=Severity.critical,
        confidence="high",
        root_cause=(
            "The vulnerable Legal Request Service discloses synthetic user "
            "data in response to government requests without verifying the "
            "presence of a valid legal basis or court order."
        ),
        security_impact=(
            "Synthetic user data can be disclosed to government entities "
            "without proper legal authorization."
        ),
        recommended_action=(
            "Verify the request has a valid legal basis before disclosing "
            "any synthetic user data."
        ),
        remediation_title="Enforce legal basis verification",
        remediation_action_type="Legal compliance",
        remediation_change=(
            "Require a valid legal basis (court order or equivalent) before "
            "processing a government data request and return HTTP 403 otherwise."
        ),
        remediation_benefit="Government requests without legal basis are rejected.",
        remediation_side_effects=(
            "Requests lacking legal basis receive HTTP 403.",
            "Government request workflows must include legal basis documentation.",
        ),
        verification_test=(
            "Repeat the government request without a legal basis and require "
            "HTTP 403."
        ),
        expected_status=403,
        test_kind="government_request",
    ),
    "SCN-008": ScenarioDefinition(
        scenario_id="SCN-008",
        name="Malicious Misbehaving Bot",
        category="Bot Security",
        objective=(
            "Request user message history from a bot that is only authorized "
            "for weather data. Correct behavior is HTTP 403."
        ),
        description=(
            "Controlled bot permission abuse scenario. An analytics bot "
            "declared for aggregate statistics attempts to access private "
            "user message history, exceeding its declared permission scope."
        ),
        affected_component=TwinComponentName.bot_management_service,
        classification="Excessive Bot Permissions",
        severity=Severity.high,
        confidence="high",
        root_cause=(
            "The vulnerable Bot Management Service does not enforce the "
            "bot's declared permission scope, allowing it to access data "
            "beyond its authorized purpose."
        ),
        security_impact=(
            "A bot with a declared purpose of aggregate statistics can "
            "access private user message history and user profiles."
        ),
        recommended_action=(
            "Enforce declared bot permission scope and reject data access "
            "requests that exceed the bot's authorized permissions."
        ),
        remediation_title="Enforce bot permission scope",
        remediation_action_type="Access control",
        remediation_change=(
            "Check the bot's declared permissions against the requested "
            "data type and return HTTP 403 when the request exceeds the "
            "bot's authorized scope."
        ),
        remediation_benefit="Bots are restricted to their declared permission scope.",
        remediation_side_effects=(
            "Bots exceeding their declared scope receive HTTP 403.",
            "Bot permission changes require explicit registration updates.",
        ),
        verification_test=(
            "Repeat the bot data access request for message history and "
            "require HTTP 403."
        ),
        expected_status=403,
        test_kind="malicious_bot",
    ),
    "SCN-009": ScenarioDefinition(
        scenario_id="SCN-009",
        name="New Feature Safety Testing",
        category="Safety Testing",
        objective=(
            "Use the AI summarization feature to access private messages "
            "beyond its declared scope. Correct behavior is HTTP 403."
        ),
        description=(
            "Controlled new-feature safety test. Before deploying an "
            "AI-powered message summarization feature, the Digital Twin "
            "verifies that the feature cannot access private messages "
            "beyond its declared public-group scope."
        ),
        affected_component=TwinComponentName.feature_service,
        classification="Feature Scope Violation",
        severity=Severity.high,
        confidence="high",
        root_cause=(
            "The vulnerable Feature Service does not enforce the feature's "
            "declared data scope, allowing the AI summarization feature to "
            "access private user messages."
        ),
        security_impact=(
            "A feature declared for public group message summarization can "
            "access private user messages and expose them to an external "
            "AI model."
        ),
        recommended_action=(
            "Enforce the feature's declared data scope and reject access "
            "to data outside the declared boundary."
        ),
        remediation_title="Enforce feature data scope boundary",
        remediation_action_type="Feature safety control",
        remediation_change=(
            "Verify the feature's declared scope before processing data "
            "requests and return HTTP 403 when the feature attempts to "
            "access data beyond its declared boundary."
        ),
        remediation_benefit="Features are restricted to their declared data scope.",
        remediation_side_effects=(
            "Feature requests exceeding the declared scope receive HTTP 403.",
            "New features must declare and register their data scope.",
        ),
        verification_test=(
            "Repeat the summarization request targeting private messages "
            "and require HTTP 403."
        ),
        expected_status=403,
        test_kind="feature_safety",
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
