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
from services.evidence_service import (
    apply_hash_chain_to_run,
    snapshot_twin,
)
from services.policy_service import (
    record_validation_policy,
    record_verification_policy,
)
from services.run_service import (
    fail_run,
    get_current_run,
    start_run,
)
from services.twin_service import set_running


ProgressCallback = Callable[[str], None]


def _progress(
    callback: ProgressCallback | None,
    message: str,
) -> None:
    if callback is not None:
        callback(message)


def _snapshot(
    trigger: str,
) -> None:
    run = get_current_run()

    if not run:
        return

    snapshot_twin(
        run_id=run.run_id,
        twin=st.session_state.twin,
        phase=st.session_state.phase,
        trigger=trigger,
    )


def start_security_validation(
    progress: ProgressCallback | None = None,
) -> dict:
    """
    Execute the controlled pre-remediation workflow.

    Any non-LLM platform failure is persisted as a failed run rather
    than leaving the current run ambiguously half-executed.
    """

    run = start_run(
        scenario_name=(
            st.session_state.selected_scenario
        ),
        objective=(
            st.session_state.scenario_objective
        ),
        model_name=(
            st.session_state.get(
                "ollama_model"
            )
        ),
        initial_twin_version=(
            st.session_state.twin[
                "version"
            ]
        ),
    )

    try:
        _progress(
            progress,
            "⚖️ Evaluating validation policy",
        )

        policy = record_validation_policy()

        if policy.outcome.value != "PERMIT":
            raise RuntimeError(
                "Policy engine blocked the run: "
                f"{policy.reason}"
            )

        set_running()

        _snapshot(
            "run_started"
        )

        _progress(
            progress,
            "🧠 Scenario Planner",
        )
        execute_planner()

        _progress(
            progress,
            "🛡️ Security Testing Agent — real HTTP test",
        )
        test = execute_security_tester()

        _progress(
            progress,
            "👁️ Observer Agent",
        )
        detected = execute_observer()

        _progress(
            progress,
            "🔍 Security Analyst — local structured LLM analysis",
        )
        analysis = execute_analyst()

        _snapshot(
            "post_analysis"
        )

        _progress(
            progress,
            "✓ Structured security analysis persisted",
        )

        return {
            "run": run,
            "test_result": test,
            "vulnerability_detected": detected,
            "analysis": analysis,
        }

    except Exception as exc:
        try:
            fail_run(
                f"Pre-remediation orchestration failed: {exc}"
            )
        except Exception:
            pass

        st.session_state.orchestration_error = str(
            exc
        )

        raise


def prepare_remediation(
    progress: ProgressCallback | None = None,
) -> dict:

    try:
        _progress(
            progress,
            "🔧 Remediation Agent — generating structured proposal",
        )

        remediation = (
            execute_remediation_agent()
        )

        _snapshot(
            "remediation_proposed"
        )

        _progress(
            progress,
            "✓ Remediation proposal persisted",
        )

        return {
            "remediation": remediation,
        }

    except Exception as exc:
        st.session_state.orchestration_error = str(
            exc
        )
        raise


def approve_and_verify(
    progress: ProgressCallback | None = None,
) -> dict:

    try:
        _progress(
            progress,
            "👤 Recording human approval",
        )

        approve_remediation()

        _snapshot(
            "human_approved"
        )

        _progress(
            progress,
            "🔧 Applying approved sandbox remediation",
        )

        verification = execute_verification()

        _progress(
            progress,
            "⚖️ Evaluating verification policy",
        )

        verification_ok = (
            verification.get("result")
            == "PASS"
            and verification.get(
                "observed_status"
            )
            == 403
        )

        verification_policy = (
            record_verification_policy(
                verification_ok
            )
        )

        _snapshot(
            "verification_complete"
        )

        run = get_current_run()

        integrity = (
            apply_hash_chain_to_run(
                run.run_id
            )
            if run
            else None
        )

        _progress(
            progress,
            "✓ Verification and evidence-integrity finalization complete",
        )

        return {
            "verification": verification,
            "verification_policy": verification_policy,
            "integrity": integrity,
        }

    except Exception as exc:
        st.session_state.orchestration_error = str(
            exc
        )
        raise
