from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from services.agent_service import (
    approve_remediation,
    execute_analyst,
    execute_observer,
    execute_planner,
    execute_remediation_agent,
    execute_security_tester,
    execute_verification,
)
from services.evidence_service import apply_hash_chain_to_run, snapshot_twin
from services.policy_service import record_validation_policy, record_verification_policy
from services.run_service import (
    complete_clean_run,
    fail_run,
    get_current_run,
    mark_verifying,
    start_run,
)
from services.scenario_registry_service import get_scenario
from services.sustainability_service import measure_agent_activity
from services.twin_service import mark_validated, mark_verifying_state, set_running


ProgressCallback = Callable[[str], None]


def _progress(callback: ProgressCallback | None, message: str) -> None:
    if callback is not None:
        callback(message)


def _snapshot(trigger: str) -> None:
    run = get_current_run()
    if not run:
        return
    snapshot_twin(
        run_id=run.run_id,
        twin=st.session_state.twin,
        phase=st.session_state.phase,
        trigger=trigger,
    )


def start_security_validation(progress: ProgressCallback | None = None) -> dict:
    scenario = get_scenario(st.session_state.selected_scenario_id)
    run = start_run(
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        objective=scenario.objective,
        model_name=st.session_state.get("ollama_model"),
        initial_twin_version=st.session_state.twin["version"],
    )

    try:
        _progress(progress, "⚖️ Evaluating validation policy")
        policy = record_validation_policy(scenario.scenario_id)
        if policy.outcome.value != "PERMIT":
            raise RuntimeError(f"Policy engine blocked the run: {policy.reason}")

        set_running()
        _snapshot("run_started")

        _progress(progress, "🧠 Scenario Planner · CodeCarbon tracking")
        measure_agent_activity(
            "Scenario Planner",
            "O1 · Plan",
            execute_planner,
        )
        _snapshot("planning_complete")

        _progress(progress, "🛡️ Security Testing Agent · CodeCarbon tracking")
        test = measure_agent_activity(
            "Security Testing Agent",
            "O2 · Detect",
            execute_security_tester,
        )
        _snapshot("security_test_complete")

        _progress(progress, "👁️ Observer Agent · CodeCarbon tracking")
        detected = measure_agent_activity(
            "Observer Agent",
            "O2 · Detect",
            execute_observer,
        )
        _snapshot("observation_complete")

        if not detected:
            _progress(progress, "✅ Secure behavior already present — no remediation required")
            mark_validated()
            complete_clean_run(test, st.session_state.twin["version"])
            _snapshot("validation_complete_no_finding")
            apply_hash_chain_to_run(run.run_id)
            return {
                "run": run,
                "test_result": test,
                "vulnerability_detected": False,
                "analysis": None,
            }

        _progress(progress, "🔍 Security Analyst · local LLM + CodeCarbon tracking")
        analysis = measure_agent_activity(
            "Security Analyst",
            "O2 · Detect",
            execute_analyst,
        )
        _snapshot("post_analysis")
        _progress(progress, "✓ Structured security analysis and sustainability telemetry persisted")

        return {
            "run": run,
            "test_result": test,
            "vulnerability_detected": True,
            "analysis": analysis,
        }
    except Exception as exc:
        try:
            fail_run(f"Pre-remediation orchestration failed: {exc}")
        except Exception:
            pass
        st.session_state.orchestration_error = str(exc)
        raise


def prepare_remediation(progress: ProgressCallback | None = None) -> dict:
    try:
        _progress(progress, "🔧 Remediation Agent · CodeCarbon tracking")
        remediation = measure_agent_activity(
            "Remediation Agent",
            "O3 · Remediate",
            execute_remediation_agent,
        )
        _snapshot("remediation_proposed")
        _progress(progress, "✓ Remediation proposal and sustainability telemetry persisted")
        return {"remediation": remediation}
    except Exception as exc:
        st.session_state.orchestration_error = str(exc)
        raise


def approve_and_verify(progress: ProgressCallback | None = None) -> dict:
    scenario = get_scenario(st.session_state.selected_scenario_id)
    try:
        _progress(progress, "👤 Recording human approval")
        approve_remediation()
        _snapshot("human_approved")

        _progress(progress, "🔧 Applying approved remediation and measuring verification")
        mark_verifying()
        mark_verifying_state()
        _snapshot("verification_started")

        verification = measure_agent_activity(
            "Verification Agent",
            "O4 · Verify",
            execute_verification,
        )

        _progress(progress, "⚖️ Evaluating verification policy")
        verification_ok = (
            verification.get("result") == "PASS"
            and verification.get("observed_status") == verification.get("expected_status")
        )
        verification_policy = record_verification_policy(
            scenario.scenario_id,
            verification_ok,
        )
        _snapshot("verification_complete")

        run = get_current_run()
        integrity = apply_hash_chain_to_run(run.run_id) if run else None
        _progress(progress, "✓ Verification, CodeCarbon telemetry and evidence integrity finalised")

        return {
            "verification": verification,
            "verification_policy": verification_policy,
            "integrity": integrity,
        }
    except Exception as exc:
        st.session_state.orchestration_error = str(exc)
        raise
