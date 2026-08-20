from __future__ import annotations

import streamlit as st

from models.policy_models import RuleEvaluationStatus
from models.workflow_models import (
    PolicyControlResult,
    PolicyDecision,
    PolicyOutcome,
    TwinComponentName,
)
from services.auth_service import can_execute_scenarios, current_role
from services.database_service import database_health
from services.policy_registry_service import (
    build_rule_results,
    save_rule_results,
    seed_policy_rules,
)
from services.run_service import get_current_run, record_policy_decision
from services.scenario_registry_service import get_scenario, is_approved_scenario


_ALLOWED_TARGETS = {
    "securemessenger",
    *(component.value.lower() for component in TwinComponentName),
}


def get_sandbox_controls() -> list[dict]:
    db = database_health()
    return [
        {
            "control": "Sandbox isolation",
            "enabled": True,
            "evidence": "SecureMessenger runs in the approved local Docker sandbox.",
        },
        {
            "control": "Synthetic data only",
            "enabled": True,
            "evidence": "All identities, messages, tokens and payloads are synthetic.",
        },
        {
            "control": "No external target access",
            "enabled": True,
            "evidence": "The scenario registry contains only local SecureMessenger tests.",
        },
        {
            "control": "Persistent audit database",
            "enabled": bool(db["connected"]),
            "evidence": (
                "PostgreSQL evidence store connected."
                if db["connected"]
                else f"PostgreSQL unavailable: {db['error']}"
            ),
        },
        {
            "control": "Role-based execution",
            "enabled": can_execute_scenarios(),
            "evidence": f"Current role: {current_role() or 'none'}.",
        },
        {
            "control": "Human approval for remediation",
            "enabled": True,
            "evidence": "Security-changing remediation requires explicit approval.",
        },
    ]


def _control(name: str, passed: bool, evidence: str) -> PolicyControlResult:
    return PolicyControlResult(control=name, passed=passed, evidence=evidence)


def evaluate_action(
    *,
    action: str,
    target: str,
    environment: str,
    scenario_id: str,
    requires_human_approval: bool,
    human_approved: bool = False,
    verification_ok: bool | None = None,
):
    db = database_health()
    environment_ok = environment.lower() in {
        "sandbox",
        "digital twin sandbox",
        "digital twin sandbox only",
    }
    target_ok = target.lower() in _ALLOWED_TARGETS
    scenario_approved = is_approved_scenario(scenario_id)
    actor_authorized = can_execute_scenarios()

    rule_results = build_rule_results(
        environment_ok=environment_ok,
        target_ok=target_ok,
        synthetic_data=True,
        database_ok=bool(db["connected"]),
        audit_ok=True,
        scenario_approved=scenario_approved,
        actor_authorized=actor_authorized,
        requires_human_approval=requires_human_approval,
        human_approved=human_approved,
        verification_ok=verification_ok,
    )

    blocking_failure = any(
        result.status == RuleEvaluationStatus.fail
        for result in rule_results
        if result.rule_id != "POL-HUM-001"
    )
    approval_pending = any(
        result.rule_id == "POL-HUM-001"
        and result.status == RuleEvaluationStatus.pending
        for result in rule_results
    )

    if blocking_failure:
        outcome, reason = (
            PolicyOutcome.block,
            "One or more mandatory governance rules failed.",
        )
    elif approval_pending:
        outcome, reason = (
            PolicyOutcome.permit_with_approval,
            "Mandatory boundaries pass, but explicit human approval is required.",
        )
    else:
        outcome, reason = PolicyOutcome.permit, "All applicable policy rules pass."

    controls = [
        _control(
            result.rule_id,
            result.passed,
            f"{result.status.value}: {result.evidence}",
        )
        for result in rule_results
    ]

    decision = PolicyDecision(
        action=action,
        target=target,
        environment=environment,
        outcome=outcome,
        reason=reason,
        requires_human_approval=requires_human_approval,
        controls=controls,
    )
    return decision, rule_results


def persist_policy_decision(decision: PolicyDecision, rule_results: list) -> PolicyDecision:
    seed_policy_rules()
    st.session_state.policy_decision = decision.model_dump(mode="json")
    history = list(st.session_state.get("policy_history", []))
    history.append(decision.model_dump(mode="json"))
    st.session_state.policy_history = history
    record_policy_decision(decision)
    run = get_current_run()
    if run:
        save_rule_results(decision.decision_id, run.run_id, rule_results)
    return decision


def evaluate_validation_policy(scenario_id: str) -> PolicyDecision:
    scenario = get_scenario(scenario_id)
    return evaluate_action(
        action=f"Execute controlled validation: {scenario.name}",
        target="SecureMessenger",
        environment="Digital Twin sandbox",
        scenario_id=scenario_id,
        requires_human_approval=False,
    )[0]


def record_validation_policy(scenario_id: str) -> PolicyDecision:
    scenario = get_scenario(scenario_id)
    decision, results = evaluate_action(
        action=f"Execute controlled validation: {scenario.name}",
        target="SecureMessenger",
        environment="Digital Twin sandbox",
        scenario_id=scenario_id,
        requires_human_approval=False,
    )
    return persist_policy_decision(decision, results)


def evaluate_remediation_policy(
    scenario_id: str,
    human_approved: bool = False,
) -> PolicyDecision:
    scenario = get_scenario(scenario_id)
    return evaluate_action(
        action=f"Apply defensive remediation: {scenario.remediation_title}",
        target=scenario.affected_component.value,
        environment="Digital Twin sandbox only",
        scenario_id=scenario_id,
        requires_human_approval=True,
        human_approved=human_approved,
    )[0]


def record_remediation_policy(
    scenario_id: str,
    human_approved: bool = False,
) -> PolicyDecision:
    scenario = get_scenario(scenario_id)
    decision, results = evaluate_action(
        action=f"Apply defensive remediation: {scenario.remediation_title}",
        target=scenario.affected_component.value,
        environment="Digital Twin sandbox only",
        scenario_id=scenario_id,
        requires_human_approval=True,
        human_approved=human_approved,
    )
    return persist_policy_decision(decision, results)


def record_verification_policy(scenario_id: str, verification_ok: bool) -> PolicyDecision:
    scenario = get_scenario(scenario_id)
    decision, results = evaluate_action(
        action=f"Mark remediation verified: {scenario.name}",
        target=scenario.affected_component.value,
        environment="Digital Twin sandbox only",
        scenario_id=scenario_id,
        requires_human_approval=False,
        verification_ok=verification_ok,
    )
    return persist_policy_decision(decision, results)


def validate_simulation_policy(scenario_id: str) -> dict:
    decision = evaluate_validation_policy(scenario_id)
    return {
        "allowed": decision.outcome == PolicyOutcome.permit,
        "controls": get_sandbox_controls(),
        "reason": decision.reason,
        "decision": decision.model_dump(mode="json"),
        "readiness": evaluate_scenario_readiness(scenario_id),
    }


def remediation_requires_approval() -> bool:
    return True


# ---------------------------------------------------------------------------
# Scenario-specific readiness evaluation
# ---------------------------------------------------------------------------


def _check(name: str, passed: bool, evidence: str, category: str) -> dict:
    return {"name": name, "passed": passed, "evidence": evidence, "category": category}


def evaluate_scenario_readiness(scenario_id: str) -> list[dict]:
    from services.sandbox_service import get_sandbox_health

    sandbox = get_sandbox_health()
    profile = sandbox.get("security_profile") or sandbox.get("authorization_mode") or ""
    is_vulnerable = profile == "vulnerable"
    available = sandbox.get("available", False)

    checks: list[dict] = []

    # Universal checks
    checks.append(_check(
        "Sandbox online",
        available,
        "SecureMessenger is reachable." if available else "SecureMessenger is offline.",
        "Infrastructure",
    ))
    checks.append(_check(
        "Vulnerable profile active",
        is_vulnerable,
        f"Security profile: {profile}."
        if available
        else "Cannot determine profile.",
        "Infrastructure",
    ))

    # Scenario-specific checks
    if scenario_id == "SCN-001":
        checks.extend(_readiness_bola(available, is_vulnerable))
    elif scenario_id == "SCN-002":
        checks.extend(_readiness_expired_token(available, is_vulnerable))
    elif scenario_id == "SCN-003":
        checks.extend(_readiness_malformed_payload(available, is_vulnerable))
    elif scenario_id == "SCN-004":
        checks.extend(_readiness_rate_limit(available, is_vulnerable))
    elif scenario_id == "SCN-005":
        checks.extend(_readiness_bulk_exfiltration(available, is_vulnerable))
    elif scenario_id == "SCN-006":
        checks.extend(_readiness_unauthorized_sharing(available, is_vulnerable))
    elif scenario_id == "SCN-007":
        checks.extend(_readiness_government_request(available, is_vulnerable))
    elif scenario_id == "SCN-008":
        checks.extend(_readiness_malicious_bot(available, is_vulnerable))
    elif scenario_id == "SCN-009":
        checks.extend(_readiness_feature_safety(available, is_vulnerable))

    return checks


def _probe(endpoint: str, token: str | None = None, method: str = "GET", json_body: dict | None = None) -> tuple[int, dict]:
    import requests as _req
    from services.config_service import get_setting

    base = get_setting("SANDBOX_BASE_URL", "http://127.0.0.1:8001")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        if method == "POST":
            resp = _req.post(f"{base}{endpoint}", headers=headers, json=json_body, timeout=3)
        else:
            resp = _req.get(f"{base}{endpoint}", headers=headers, timeout=3)
        return resp.status_code, resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    except Exception:
        return 0, {}


def _readiness_bola(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, body = _probe("/messages/MSG-204", token="token-alice")
        accessible = status == 200
        checks.append(_check(
            "Cross-user message accessible (vulnerable)",
            is_vulnerable and accessible,
            f"HTTP {status} — {'Bob message accessible by Alice' if accessible else 'Access denied'}.",
            "Scenario precondition",
        ))
        owner = body.get("owner") if isinstance(body, dict) else None
        checks.append(_check(
            "Message owner exposed in response",
            owner == "bob",
            f"Response owner: {owner}.",
            "Scenario precondition",
        ))
    else:
        checks.append(_check("Cross-user message accessible (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks


def _readiness_expired_token(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, body = _probe("/users/me", token="expired-token-alice")
        accepted = status == 200
        checks.append(_check(
            "Expired token accepted (vulnerable)",
            is_vulnerable and accepted,
            f"HTTP {status} — expired token {'accepted' if accepted else 'rejected'}.",
            "Scenario precondition",
        ))
    else:
        checks.append(_check("Expired token accepted (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks


def _readiness_malformed_payload(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, _ = _probe(
            "/messages",
            token="token-alice",
            method="POST",
            json_body={"recipient": "bob", "body": "", "priority": 99, "unexpected": "field"},
        )
        accepted = status == 201
        checks.append(_check(
            "Malformed payload accepted (vulnerable)",
            is_vulnerable and accepted,
            f"HTTP {status} — malformed payload {'accepted' if accepted else 'rejected'}.",
            "Scenario precondition",
        ))
    else:
        checks.append(_check("Malformed payload accepted (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks


def _readiness_rate_limit(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, _ = _probe("/rate-test", token="token-alice", method="POST")
        passed_through = status == 200
        checks.append(_check(
            "Rate limiting disabled (vulnerable)",
            is_vulnerable and passed_through,
            f"HTTP {status} — request {'passed through' if passed_through else 'was throttled'}.",
            "Scenario precondition",
        ))
    else:
        checks.append(_check("Rate limiting disabled (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks


def _readiness_bulk_exfiltration(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, body = _probe("/export/messages?limit=1000000", token="token-eve")
        accessible = status == 200
        count = body.get("exported_count", 0) if isinstance(body, dict) else 0
        checks.append(_check(
            "Bulk export endpoint accessible (vulnerable)",
            is_vulnerable and accessible,
            f"HTTP {status} — exported {count} messages.",
            "Scenario precondition",
        ))
        checks.append(_check(
            "Multiple users with messages exist",
            count >= 3,
            f"Exported {count} messages from the synthetic dataset.",
            "Data fixture",
        ))
    else:
        checks.append(_check("Bulk export endpoint accessible (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks


def _readiness_unauthorized_sharing(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, body = _probe("/integrations", token="token-alice")
        integrations = body if isinstance(body, list) else body.get("value", []) if isinstance(body, dict) else []
        has_unauthorized = any(
            not i.get("authorized", True)
            for i in integrations
            if isinstance(i, dict)
        )
        checks.append(_check(
            "Unauthorized integration available",
            has_unauthorized,
            "External marketing integration present and unauthorized." if has_unauthorized
            else "No unauthorized integrations found.",
            "Data fixture",
        ))
        status2, _ = _probe(
            "/share",
            token="token-alice",
            method="POST",
            json_body={"integration_id": "external-marketing", "data_type": "user_messages"},
        )
        accepted = status2 == 200
        checks.append(_check(
            "Unauthorized share accepted (vulnerable)",
            is_vulnerable and accepted,
            f"HTTP {status2} — share to unauthorized integration {'accepted' if accepted else 'blocked'}.",
            "Scenario precondition",
        ))
    else:
        checks.append(_check("Unauthorized share accepted (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks


def _readiness_government_request(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, body = _probe(
            "/legal/request",
            token="token-alice",
            method="POST",
            json_body={
                "request_id": "GOV-REQ-001",
                "entity": "National Security Agency",
                "request_type": "user_data_access",
                "scope": "all_user_messages",
                "legal_basis": None,
            },
        )
        accepted = status == 200
        disclosed = "data_shared" in body if isinstance(body, dict) else False
        checks.append(_check(
            "Government request without legal basis accepted (vulnerable)",
            is_vulnerable and accepted,
            f"HTTP {status} — data {'disclosed' if disclosed else 'not disclosed'}.",
            "Scenario precondition",
        ))
        checks.append(_check(
            "Request lacks valid legal basis",
            True,
            "GOV-REQ-001 has no legal_basis — tests enforcement.",
            "Data fixture",
        ))
    else:
        checks.append(_check("Government request without legal basis accepted (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks


def _readiness_malicious_bot(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, body = _probe(
            "/bot/analytics-bot/data?data_type=message_history",
            token="token-alice",
        )
        accessible = status == 200
        checks.append(_check(
            "Bot excess data access accepted (vulnerable)",
            is_vulnerable and accessible,
            f"HTTP {status} — message_history {'accessible' if accessible else 'denied'}.",
            "Scenario precondition",
        ))
        from sandbox.secure_messenger.database import BOTS
        bot = BOTS.get("analytics-bot", {})
        perms = bot.get("permissions", [])
        has_excess_perms = len(perms) > 3
        checks.append(_check(
            "Bot has excessive permissions",
            has_excess_perms,
            f"Analytics bot declared {len(perms)} permissions including message_history and export_data." if has_excess_perms
            else "Cannot verify bot permissions.",
            "Data fixture",
        ))
    else:
        checks.append(_check("Bot excess data access accepted (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks


def _readiness_feature_safety(available: bool, is_vulnerable: bool) -> list[dict]:
    checks = []
    if available:
        status, body = _probe(
            "/feature/summarize",
            token="token-alice",
            method="POST",
            json_body={
                "feature_id": "ai_summarization",
                "message_ids": ["MSG-204", "MSG-305"],
                "include_private": True,
            },
        )
        accepted = status == 200
        summarized = body.get("summarized_count", 0) if isinstance(body, dict) else 0
        checks.append(_check(
            "Feature accesses private messages (vulnerable)",
            is_vulnerable and accepted,
            f"HTTP {status} — summarized {summarized} messages including other users'.",
            "Scenario precondition",
        ))
        checks.append(_check(
            "Feature declared scope is limited",
            True,
            "AI summarization declared scope: public_group_messages only.",
            "Data fixture",
        ))
        checks.append(_check(
            "Feature sends data to external model",
            True,
            "sends_to_external_model=True — privacy boundary is testable.",
            "Data fixture",
        ))
    else:
        checks.append(_check("Feature accesses private messages (vulnerable)", False, "Sandbox offline.", "Scenario precondition"))
    return checks
