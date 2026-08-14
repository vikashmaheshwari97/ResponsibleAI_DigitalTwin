from __future__ import annotations
import streamlit as st
from models.policy_models import RuleEvaluationStatus
from models.workflow_models import PolicyControlResult, PolicyDecision, PolicyOutcome
from services.database_service import database_health
from services.policy_registry_service import build_rule_results, save_rule_results, seed_policy_rules
from services.run_service import get_current_run, record_policy_decision

def get_sandbox_controls() -> list[dict]:
    db = database_health()
    return [
        {"control":"Sandbox isolation","enabled":True,"evidence":"SecureMessenger runs in a dedicated localhost Docker sandbox."},
        {"control":"Synthetic data only","enabled":True,"evidence":"Alice, Bob, Charlie and all messages are synthetic PoC records."},
        {"control":"No external target access","enabled":True,"evidence":"The workflow targets only local SecureMessenger."},
        {"control":"Persistent audit database","enabled":bool(db["connected"]),"evidence":"PostgreSQL rai_twin connected." if db["connected"] else f"PostgreSQL unavailable: {db['error']}"},
        {"control":"Human approval for remediation","enabled":True,"evidence":"Security-changing remediation requires explicit approval."},
    ]

def _control(name: str, passed: bool, evidence: str) -> PolicyControlResult:
    return PolicyControlResult(control=name, passed=passed, evidence=evidence)

def evaluate_action(action: str, target: str, environment: str, requires_human_approval: bool, human_approved: bool=False, verification_ok: bool|None=None):
    db = database_health()
    environment_ok = environment.lower() in {"sandbox","digital twin sandbox","digital twin sandbox only"}
    target_ok = target.lower() in {"securemessenger","message api","securemessenger/message api"}
    rule_results = build_rule_results(
        environment_ok=environment_ok, target_ok=target_ok, synthetic_data=True,
        database_ok=bool(db["connected"]), audit_ok=True,
        requires_human_approval=requires_human_approval, human_approved=human_approved,
        verification_ok=verification_ok,
    )
    blocking_failure = any(r.status == RuleEvaluationStatus.fail for r in rule_results if r.rule_id != "POL-HUM-001")
    approval_pending = any(r.rule_id == "POL-HUM-001" and r.status == RuleEvaluationStatus.pending for r in rule_results)
    if blocking_failure:
        outcome, reason = PolicyOutcome.block, "One or more mandatory policy rules failed."
    elif approval_pending:
        outcome, reason = PolicyOutcome.permit_with_approval, "Mandatory boundaries pass, but explicit human approval is required."
    else:
        outcome, reason = PolicyOutcome.permit, "All applicable policy rules pass."
    controls = [_control(r.rule_id, r.passed, f"{r.status.value}: {r.evidence}") for r in rule_results]
    return PolicyDecision(action=action,target=target,environment=environment,outcome=outcome,reason=reason,requires_human_approval=requires_human_approval,controls=controls), rule_results

def persist_policy_decision(decision: PolicyDecision, rule_results: list) -> PolicyDecision:
    seed_policy_rules()
    st.session_state.policy_decision = decision.model_dump(mode="json")
    history = list(st.session_state.get("policy_history", [])); history.append(decision.model_dump(mode="json")); st.session_state.policy_history = history
    record_policy_decision(decision)
    run = get_current_run()
    if run: save_rule_results(decision.decision_id, run.run_id, rule_results)
    return decision

def evaluate_validation_policy() -> PolicyDecision:
    return evaluate_action("Execute controlled authorization validation","SecureMessenger","Digital Twin sandbox",False)[0]

def record_validation_policy() -> PolicyDecision:
    d,r=evaluate_action("Execute controlled authorization validation","SecureMessenger","Digital Twin sandbox",False); return persist_policy_decision(d,r)

def evaluate_remediation_policy(human_approved: bool=False) -> PolicyDecision:
    return evaluate_action("Apply object-level authorization remediation","Message API","Digital Twin sandbox only",True,human_approved)[0]

def record_remediation_policy(human_approved: bool=False) -> PolicyDecision:
    d,r=evaluate_action("Apply object-level authorization remediation","Message API","Digital Twin sandbox only",True,human_approved); return persist_policy_decision(d,r)

def record_verification_policy(verification_ok: bool) -> PolicyDecision:
    d,r=evaluate_action("Mark remediation verified","Message API","Digital Twin sandbox only",False,False,verification_ok); return persist_policy_decision(d,r)

def validate_simulation_policy() -> dict:
    d=evaluate_validation_policy(); return {"allowed":d.outcome==PolicyOutcome.permit,"controls":get_sandbox_controls(),"reason":d.reason,"decision":d.model_dump(mode="json")}

def remediation_requires_approval() -> bool: return True
