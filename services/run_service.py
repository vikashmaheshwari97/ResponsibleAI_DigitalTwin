from __future__ import annotations

from datetime import datetime, timezone
import streamlit as st
from models.workflow_models import FindingAnalysis, PolicyDecision, RemediationPlan, RunStatus, SimulationRun
from services.repository_service import (
    save_finding, save_human_decision, save_policy_decision, save_remediation,
    save_run, save_security_test, update_run_lifecycle,
)

_ALLOWED_TRANSITIONS = {
    RunStatus.created: {RunStatus.running, RunStatus.aborted},
    RunStatus.running: {RunStatus.vulnerable, RunStatus.failed, RunStatus.interrupted, RunStatus.aborted},
    RunStatus.vulnerable: {RunStatus.awaiting_approval, RunStatus.failed, RunStatus.interrupted, RunStatus.aborted},
    RunStatus.awaiting_approval: {RunStatus.remediating, RunStatus.rejected, RunStatus.interrupted, RunStatus.aborted},
    RunStatus.remediating: {RunStatus.verifying, RunStatus.failed, RunStatus.interrupted, RunStatus.aborted},
    RunStatus.verifying: {RunStatus.secured, RunStatus.failed, RunStatus.interrupted, RunStatus.aborted},
    RunStatus.secured: set(), RunStatus.failed: set(), RunStatus.rejected: set(),
    RunStatus.interrupted: set(), RunStatus.aborted: set(),
}

def _now() -> str: return datetime.now(timezone.utc).isoformat()

def _save(run: SimulationRun) -> SimulationRun:
    st.session_state.current_run = run.model_dump(mode="json")
    save_run(run)
    return run

def get_current_run() -> SimulationRun | None:
    raw = st.session_state.get("current_run")
    return SimulationRun.model_validate(raw) if raw else None

def start_run(scenario_name: str, objective: str, model_name: str | None, initial_twin_version: str) -> SimulationRun:
    run = SimulationRun(
        scenario_name=scenario_name, objective=objective, model_name=model_name,
        initial_twin_version=initial_twin_version, status=RunStatus.running,
        last_transition_at=_now(),
    )
    return _save(run)

def transition_run(new_status: RunStatus | str, *, failure_reason: str | None = None, abort_reason: str | None = None) -> SimulationRun | None:
    run = get_current_run()
    if not run: return None
    new_status = RunStatus(new_status)
    current = RunStatus(run.status)
    if new_status == current: return run
    if new_status not in _ALLOWED_TRANSITIONS[current]:
        raise RuntimeError(f"Invalid run lifecycle transition: {current.value} -> {new_status.value}")
    run.status = new_status
    run.last_transition_at = _now()
    run.failure_reason = failure_reason
    run.abort_reason = abort_reason
    if new_status == RunStatus.interrupted: run.interrupted_at = _now()
    if new_status in {RunStatus.secured, RunStatus.failed, RunStatus.rejected, RunStatus.interrupted, RunStatus.aborted}:
        run.completed_at = run.completed_at or _now()
    return _save(run)

def record_policy_decision(decision: PolicyDecision) -> None:
    run = get_current_run()
    if not run: return
    if any(item.decision_id == decision.decision_id for item in run.policy_decisions): return
    run.policy_decisions.append(decision)
    save_policy_decision(run.run_id, decision)
    _save(run)

def record_initial_test(test_result: dict) -> None:
    run = get_current_run()
    if not run: return
    run.initial_security_test = test_result
    save_security_test(run.run_id, "initial", test_result)
    _save(run)
    if test_result.get("vulnerability_detected"): transition_run(RunStatus.vulnerable)

def record_structured_finding(finding: FindingAnalysis) -> None:
    run = get_current_run()
    if not run: return
    run.structured_finding = finding
    save_finding(run.run_id, finding)
    _save(run)

def record_remediation(remediation: RemediationPlan) -> None:
    run = get_current_run()
    if not run: return
    run.remediation_plan = remediation
    save_remediation(run.run_id, remediation)
    _save(run)
    transition_run(RunStatus.awaiting_approval)

def record_human_decision(decision: str) -> None:
    run = get_current_run()
    if not run: return
    run.human_decision = decision
    remediation_id = run.remediation_plan.remediation_id if run.remediation_plan else None
    save_human_decision(run.run_id, remediation_id, decision)
    _save(run)
    if decision.lower() == "rejected": transition_run(RunStatus.rejected)

def mark_remediating() -> None: transition_run(RunStatus.remediating)
def mark_verifying() -> None: transition_run(RunStatus.verifying)

def complete_run(verification: dict, final_twin_version: str) -> None:
    run = get_current_run()
    if not run: return
    run.verification_test = verification
    run.final_twin_version = final_twin_version
    passed = verification.get("result") == "PASS" and verification.get("observed_status") == 403
    run.result = "PASS" if passed else "FAIL"
    save_security_test(run.run_id, "verification", verification)
    _save(run)
    if passed:
        transition_run(RunStatus.secured)
    else:
        transition_run(RunStatus.failed, failure_reason="Verification did not produce the required HTTP 403.")

def fail_run(reason: str) -> None: transition_run(RunStatus.failed, failure_reason=reason)

def interrupt_persisted_run(run_id: str, reason: str) -> None:
    update_run_lifecycle(run_id, status=RunStatus.interrupted.value, failure_reason=reason, interrupted_at=datetime.now(timezone.utc))

def abort_persisted_run(run_id: str, reason: str) -> None:
    update_run_lifecycle(run_id, status=RunStatus.aborted.value, abort_reason=reason)
