from datetime import datetime

import streamlit as st

from models.workflow_models import FindingAnalysis, RemediationPlan
from services.audit_service import add_audit_event
from services.ollama_service import analyse_security_finding, propose_remediation
from services.policy_service import (
    record_remediation_policy,
)
from services.repository_service import save_agent_event
from services.run_service import (
    complete_run,
    get_current_run,
    mark_remediating,
    mark_verifying,
    record_human_decision,
    record_initial_test,
    record_remediation,
    record_structured_finding,
)
from services.sandbox_service import apply_secure_mode, get_sandbox_health
from services.security_test_service import (
    format_security_evidence,
    run_cross_user_message_test,
)
from services.twin_service import (
    mark_secured,
    mark_vulnerability,
    reject_remediation_state,
    set_remediation_proposal,
    sync_twin_from_sandbox,
)


def _current_run_id() -> str | None:
    run = get_current_run()
    return run.run_id if run else None


def add_agent_event(
    agent: str,
    action: str,
    status: str = "Completed",
    event_type: str = "Agent",
) -> dict:
    event = {
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Agent": agent,
        "Action": action,
        "Status": status,
        "Type": event_type,
    }

    st.session_state.agent_events.append(event)

    run_id = _current_run_id()
    if run_id:
        save_agent_event(
            run_id=run_id,
            agent=agent,
            action=action,
            status=status,
            event_type=event_type,
        )

    return event


def update_agent_status(agent: str, status: str) -> None:
    st.session_state.agent_status[agent] = status


def execute_planner() -> None:
    update_agent_status("Scenario Planner", "Completed")

    add_agent_event(
        "Scenario Planner",
        "Created the controlled cross-user authorization validation plan.",
    )
    add_audit_event(
        actor="Scenario Planner",
        action="Controlled security scenario generated",
        category="Agent",
        details=st.session_state.selected_scenario,
    )


def execute_security_tester() -> dict:
    update_agent_status("Security Testing Agent", "Running")

    try:
        result = run_cross_user_message_test()
        st.session_state.last_security_test = result
        record_initial_test(result)

        add_agent_event(
            "Security Testing Agent",
            (
                "Executed a real HTTP authorization validation against Docker "
                "SecureMessenger. "
                f"Expected HTTP {result['expected_status']}; observed "
                f"HTTP {result['observed_status']}."
            ),
        )
        add_audit_event(
            actor="Security Testing Agent",
            action="Real cross-user message authorization test executed",
            category="Security Test",
            details=(
                f"Alice requested {result['resource_id']}. Expected HTTP "
                f"{result['expected_status']}; observed HTTP "
                f"{result['observed_status']}."
            ),
        )

        update_agent_status("Security Testing Agent", "Completed")
        return result

    except Exception as exc:
        update_agent_status("Security Testing Agent", "Failed")
        add_agent_event(
            "Security Testing Agent",
            f"Sandbox test failed: {exc}",
            status="Failed",
        )
        add_audit_event(
            actor="Security Testing Agent",
            action="Sandbox test failed",
            status="Failed",
            category="Security Test",
            details=str(exc),
        )
        raise


def execute_observer() -> bool:
    update_agent_status("Observer Agent", "Running")
    result = st.session_state.get("last_security_test")

    if not result:
        update_agent_status("Observer Agent", "Failed")
        raise RuntimeError("No real security test result is available.")

    detected = bool(result["vulnerability_detected"])

    action = (
        "Observed real cross-user disclosure: Alice received Bob's "
        "MSG-204 with HTTP 200."
        if detected
        else (
            f"Cross-user access denied as expected. "
            f"Observed HTTP {result['observed_status']}."
        )
    )

    add_agent_event("Observer Agent", action)
    add_audit_event(
        actor="Observer Agent",
        action="Evaluated real HTTP test response",
        category="Observation",
        details=action,
    )

    update_agent_status("Observer Agent", "Completed")
    return detected



def execute_analyst() -> FindingAnalysis:
    """
    Execute the local structured analyst stage.

    Important behavior:
    - Ollama errors/timeouts use the deterministic structured fallback.
    - Persistence/orchestration failures mark the agent Failed and are raised.
    - The agent cannot silently remain in the Running state.
    """
    update_agent_status("Security Analyst", "Running")

    try:
        result = st.session_state.get(
            "last_security_test"
        )

        if not result:
            raise RuntimeError(
                "No real security-test evidence is available."
            )

        evidence = format_security_evidence(
            result
        )

        model = st.session_state.get(
            "ollama_model"
        )

        if model:
            try:
                analysis = analyse_security_finding(
                    model=model,
                    evidence=evidence,
                )

                source = (
                    f"Ollama structured output / {model}"
                )

            except Exception as llm_exc:
                # A slow/unavailable local model must not block the full
                # defensive workflow. The fallback is still schema-valid.
                analysis = _fallback_analysis()

                source = (
                    "Deterministic structured fallback · "
                    f"Ollama unavailable/timeout: {llm_exc}"
                )
        else:
            analysis = _fallback_analysis()
            source = (
                "Deterministic structured fallback"
            )

        st.session_state.structured_finding = (
            analysis.model_dump(
                mode="json"
            )
        )

        st.session_state.analyst_llm_output = (
            analysis.model_dump(
                mode="json"
            )
        )

        st.session_state.analyst_source = (
            source
        )

        record_structured_finding(
            analysis
        )

        if result["vulnerability_detected"]:
            mark_vulnerability()

        update_agent_status(
            "Security Analyst",
            "Completed",
        )

        add_agent_event(
            "Security Analyst",
            (
                "Generated schema-validated security analysis. "
                f"Source: {source}."
            ),
        )

        add_audit_event(
            actor="Security Analyst",
            action="Structured security analysis generated",
            category="AI Analysis",
            details=(
                f"Source: {source}; "
                f"classification={analysis.classification}; "
                f"severity={analysis.severity.value}; "
                f"confidence={analysis.confidence.value}; "
                f"component={analysis.affected_component.value}"
            ),
        )

        return analysis

    except Exception as exc:
        update_agent_status(
            "Security Analyst",
            "Failed",
        )

        # Best effort logging. Do not hide the original exception if
        # PostgreSQL/audit persistence also fails.
        try:
            add_agent_event(
                "Security Analyst",
                f"Structured analysis stage failed: {exc}",
                status="Failed",
            )

            add_audit_event(
                actor="Security Analyst",
                action="Structured security analysis failed",
                status="Failed",
                category="AI Analysis",
                details=str(exc),
            )
        except Exception:
            pass

        raise

def _fallback_analysis() -> FindingAnalysis:
    return FindingAnalysis(
        classification="Broken Object-Level Authorization",
        severity="high",
        confidence="high",
        affected_component="Message API",
        root_cause=(
            "The authenticated requester is not checked against the owner "
            "of the requested message resource."
        ),
        security_impact=(
            "One synthetic user can retrieve another synthetic user's "
            "private message."
        ),
        recommended_action=(
            "Enforce object-level ownership validation and repeat the exact "
            "same controlled HTTP test."
        ),
    )



def execute_remediation_agent() -> RemediationPlan:
    update_agent_status(
        "Remediation Agent",
        "Running",
    )

    try:
        result = (
            st.session_state.get(
                "last_security_test"
            )
            or {}
        )

        evidence = (
            format_security_evidence(result)
            if result
            else "No evidence."
        )

        finding_raw = st.session_state.get(
            "structured_finding"
        )

        finding = (
            FindingAnalysis.model_validate(
                finding_raw
            )
            if finding_raw
            else _fallback_analysis()
        )

        model = st.session_state.get(
            "ollama_model"
        )

        if model:
            try:
                recommendation = propose_remediation(
                    model=model,
                    finding=finding,
                    evidence=evidence,
                )

                source = (
                    f"Ollama structured output / {model}"
                )

            except Exception as llm_exc:
                recommendation = (
                    _fallback_remediation()
                )

                source = (
                    "Deterministic structured fallback · "
                    f"Ollama unavailable/timeout: {llm_exc}"
                )
        else:
            recommendation = (
                _fallback_remediation()
            )
            source = (
                "Deterministic structured fallback"
            )

        recommendation.requires_human_approval = (
            True
        )

        recommendation.target_environment = (
            "Digital Twin sandbox only"
        )

        st.session_state.structured_remediation = (
            recommendation.model_dump(
                mode="json"
            )
        )

        st.session_state.remediation_llm_output = (
            recommendation.model_dump(
                mode="json"
            )
        )

        st.session_state.remediation_source = (
            source
        )

        record_remediation(
            recommendation
        )

        policy = record_remediation_policy(
            human_approved=False
        )

        update_agent_status(
            "Remediation Agent",
            "Proposal Ready",
        )

        add_agent_event(
            "Remediation Agent",
            (
                "Generated schema-validated defensive remediation. "
                f"Policy outcome: {policy.outcome.value}."
            ),
        )

        add_audit_event(
            actor="Remediation Agent",
            action="Structured defensive remediation proposal generated",
            category="AI Remediation",
            details=(
                f"Source: {source}; "
                f"policy={policy.outcome.value}; "
                "human approval required."
            ),
        )

        set_remediation_proposal()

        return recommendation

    except Exception as exc:
        update_agent_status(
            "Remediation Agent",
            "Failed",
        )

        try:
            add_agent_event(
                "Remediation Agent",
                f"Remediation stage failed: {exc}",
                status="Failed",
            )

            add_audit_event(
                actor="Remediation Agent",
                action="Structured remediation generation failed",
                status="Failed",
                category="AI Remediation",
                details=str(exc),
            )
        except Exception:
            pass

        raise

def _fallback_remediation() -> RemediationPlan:
    return RemediationPlan(
        title="Enforce object-level authorization",
        target_component="Message API",
        action_type="authorization_control",
        proposed_change=(
            "Verify that the authenticated synthetic user owns the requested "
            "message before returning the resource."
        ),
        risk="low",
        expected_security_benefit=(
            "Cross-user access to private synthetic messages is denied."
        ),
        possible_side_effects=[
            "Unauthorized requests now receive HTTP 403.",
            "Existing tests must account for ownership enforcement.",
        ],
        verification_test=(
            "Repeat Alice → MSG-204 and require HTTP 403 while Alice → MSG-101 "
            "continues to return HTTP 200."
        ),
        requires_human_approval=True,
        target_environment="Digital Twin sandbox only",
    )


def approve_remediation() -> None:
    # Exactly one persisted post-approval policy decision.
    policy = record_remediation_policy(human_approved=True)

    if policy.outcome.value != "PERMIT":
        raise RuntimeError(
            f"Policy engine did not permit remediation: {policy.reason}"
        )

    st.session_state.remediation_policy_approved = True
    record_human_decision("approved")
    mark_remediating()

    add_agent_event(
        "Human Reviewer",
        "Approved the remediation for the Digital Twin sandbox only.",
        event_type="Human",
    )
    add_audit_event(
        actor="Human Reviewer",
        action="Approved remediation",
        category="Human Oversight",
        details=(
            "Approval recorded before sandbox configuration change; "
            f"policy={policy.outcome.value}."
        ),
    )


def reject_remediation() -> None:
    record_human_decision("rejected")

    add_agent_event(
        "Human Reviewer",
        "Rejected the remediation. No sandbox change was applied.",
        status="Rejected",
        event_type="Human",
    )
    add_audit_event(
        actor="Human Reviewer",
        action="Rejected remediation",
        status="Rejected",
        category="Human Oversight",
    )
    reject_remediation_state()


def execute_verification() -> dict:
    update_agent_status("Verification Agent", "Running")

    if not st.session_state.get("remediation_policy_approved"):
        update_agent_status("Verification Agent", "Failed")
        raise RuntimeError(
            "Verification cannot apply remediation without a recorded "
            "PERMIT policy decision after human approval."
        )

    mark_verifying()

    config = apply_secure_mode()
    health = get_sandbox_health()
    sync_twin_from_sandbox(health)

    add_audit_event(
        actor="Sandbox Controller",
        action="Applied approved secure authorization mode",
        category="Remediation",
        details=(
            f"SecureMessenger version {config.get('version')} / "
            f"{config.get('authorization_mode')}"
        ),
    )

    verification = run_cross_user_message_test()
    st.session_state.verification_test = verification

    passed = (
        verification["observed_status"] == 403
        and verification["result"] == "PASS"
    )

    add_agent_event(
        "Verification Agent",
        (
            "Re-ran the exact same real HTTP scenario. Expected HTTP 403; "
            f"observed HTTP {verification['observed_status']}."
        ),
        status="Completed" if passed else "Failed",
    )
    add_audit_event(
        actor="Verification Agent",
        action="Real post-remediation authorization test executed",
        status="Success" if passed else "Failed",
        category="Verification",
        details=(
            f"Expected HTTP 403; observed HTTP "
            f"{verification['observed_status']}."
        ),
    )

    if not passed:
        update_agent_status("Verification Agent", "Failed")
        raise RuntimeError(
            "Verification failed: sandbox did not return HTTP 403."
        )

    update_agent_status("Verification Agent", "Completed")
    mark_secured()
    complete_run(
        verification=verification,
        final_twin_version=st.session_state.twin["version"],
    )

    add_audit_event(
        actor="Verification Agent",
        action="Remediation verified successfully",
        category="Verification",
        details="Cross-user request is denied with HTTP 403.",
    )

    return verification
