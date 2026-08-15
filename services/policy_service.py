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
    }


def remediation_requires_approval() -> bool:
    return True
