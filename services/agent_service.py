from __future__ import annotations

from datetime import datetime

import streamlit as st

from models.workflow_models import FindingAnalysis, RemediationPlan
from services.audit_service import add_audit_event
from services.auth_service import current_username
from services.ollama_service import analyse_security_finding, propose_remediation
from services.policy_service import record_remediation_policy
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
from services.scenario_registry_service import get_scenario
from services.security_test_service import format_security_evidence, run_scenario_test
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


def _scenario():
    return get_scenario(st.session_state.selected_scenario_id)


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
    scenario = _scenario()
    update_agent_status("Scenario Planner", "Completed")
    add_agent_event(
        "Scenario Planner",
        f"Prepared approved controlled plan {scenario.scenario_id}: {scenario.name}.",
    )
    add_audit_event(
        actor="Scenario Planner",
        action="Controlled security scenario generated",
        category="Agent",
        details=f"{scenario.scenario_id} · {scenario.name}",
    )


def execute_security_tester() -> dict:
    scenario = _scenario()
    update_agent_status("Security Testing Agent", "Running")
    try:
        result = run_scenario_test(scenario.scenario_id)
        st.session_state.last_security_test = result
        record_initial_test(result)
        add_agent_event(
            "Security Testing Agent",
            (
                f"Executed real local HTTP test for {scenario.scenario_id}. "
                f"Expected HTTP {result['expected_status']}; observed HTTP "
                f"{result['observed_status']}."
            ),
        )
        add_audit_event(
            actor="Security Testing Agent",
            action="Controlled real HTTP validation executed",
            category="Security Test",
            details=(
                f"scenario={scenario.scenario_id}; resource={result['resource_id']}; "
                f"expected={result['expected_status']}; observed={result['observed_status']}"
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
            action="Controlled sandbox test failed",
            status="Failed",
            category="Security Test",
            details=str(exc),
        )
        raise


def execute_observer() -> bool:
    scenario = _scenario()
    update_agent_status("Observer Agent", "Running")
    result = st.session_state.get("last_security_test")
    if not result:
        update_agent_status("Observer Agent", "Failed")
        raise RuntimeError("No real security-test result is available.")

    detected = bool(result["vulnerability_detected"])
    if detected:
        action = (
            f"Observed expected-secure HTTP {result['expected_status']} but the vulnerable "
            f"sandbox returned HTTP {result['observed_status']} for {scenario.name}."
        )
    else:
        action = (
            f"Observed secure behavior for {scenario.name}: HTTP "
            f"{result['observed_status']}."
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


def _fallback_analysis() -> FindingAnalysis:
    scenario = _scenario()
    return FindingAnalysis(
        classification=scenario.classification,
        severity=scenario.severity,
        confidence=scenario.confidence,
        affected_component=scenario.affected_component,
        root_cause=scenario.root_cause,
        security_impact=scenario.security_impact,
        recommended_action=scenario.recommended_action,
    )


def execute_analyst() -> FindingAnalysis:
    scenario = _scenario()
    update_agent_status("Security Analyst", "Running")
    try:
        result = st.session_state.get("last_security_test")
        if not result:
            raise RuntimeError("No real security-test evidence is available.")

        evidence = format_security_evidence(result)
        model = st.session_state.get("ollama_model")
        if model:
            try:
                analysis = analyse_security_finding(
                    model=model,
                    evidence=evidence,
                    scenario=scenario,
                )
                source = f"Ollama structured output / {model}"
            except Exception as llm_exc:
                analysis = _fallback_analysis()
                source = (
                    "Deterministic structured fallback · "
                    f"Ollama unavailable/timeout: {llm_exc}"
                )
        else:
            analysis = _fallback_analysis()
            source = "Deterministic structured fallback"

        st.session_state.structured_finding = analysis.model_dump(mode="json")
        st.session_state.analyst_llm_output = analysis.model_dump(mode="json")
        st.session_state.analyst_source = source
        record_structured_finding(analysis)

        if result["vulnerability_detected"]:
            mark_vulnerability()

        update_agent_status("Security Analyst", "Completed")
        add_agent_event(
            "Security Analyst",
            f"Generated schema-validated analysis for {scenario.scenario_id}. Source: {source}.",
        )
        add_audit_event(
            actor="Security Analyst",
            action="Structured security analysis generated",
            category="AI Analysis",
            details=(
                f"scenario={scenario.scenario_id}; source={source}; "
                f"classification={analysis.classification}; severity={analysis.severity.value}; "
                f"confidence={analysis.confidence.value}; "
                f"component={analysis.affected_component.value}"
            ),
        )
        return analysis
    except Exception as exc:
        update_agent_status("Security Analyst", "Failed")
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


def _fallback_remediation() -> RemediationPlan:
    scenario = _scenario()
    return RemediationPlan(
        title=scenario.remediation_title,
        target_component=scenario.affected_component,
        action_type=scenario.remediation_action_type,
        proposed_change=scenario.remediation_change,
        risk="low",
        expected_security_benefit=scenario.remediation_benefit,
        possible_side_effects=list(scenario.remediation_side_effects),
        verification_test=scenario.verification_test,
        requires_human_approval=True,
        target_environment="Digital Twin sandbox only",
    )


def execute_remediation_agent() -> RemediationPlan:
    scenario = _scenario()
    update_agent_status("Remediation Agent", "Running")
    try:
        result = st.session_state.get("last_security_test") or {}
        evidence = format_security_evidence(result) if result else "No evidence."
        finding_raw = st.session_state.get("structured_finding")
        finding = (
            FindingAnalysis.model_validate(finding_raw)
            if finding_raw
            else _fallback_analysis()
        )
        model = st.session_state.get("ollama_model")

        if model:
            try:
                recommendation = propose_remediation(
                    model=model,
                    finding=finding,
                    evidence=evidence,
                    scenario=scenario,
                )
                source = f"Ollama structured output / {model}"
            except Exception as llm_exc:
                recommendation = _fallback_remediation()
                source = (
                    "Deterministic structured fallback · "
                    f"Ollama unavailable/timeout: {llm_exc}"
                )
        else:
            recommendation = _fallback_remediation()
            source = "Deterministic structured fallback"

        recommendation.requires_human_approval = True
        recommendation.target_environment = "Digital Twin sandbox only"
        recommendation.target_component = scenario.affected_component

        st.session_state.structured_remediation = recommendation.model_dump(mode="json")
        st.session_state.remediation_llm_output = recommendation.model_dump(mode="json")
        st.session_state.remediation_source = source
        record_remediation(recommendation)

        policy = record_remediation_policy(
            scenario.scenario_id,
            human_approved=False,
        )
        update_agent_status("Remediation Agent", "Proposal Ready")
        add_agent_event(
            "Remediation Agent",
            (
                f"Generated schema-validated defensive remediation for "
                f"{scenario.scenario_id}. Policy outcome: {policy.outcome.value}."
            ),
        )
        add_audit_event(
            actor="Remediation Agent",
            action="Structured defensive remediation proposal generated",
            category="AI Remediation",
            details=(
                f"scenario={scenario.scenario_id}; source={source}; "
                f"policy={policy.outcome.value}; human approval required"
            ),
        )
        set_remediation_proposal()
        return recommendation
    except Exception as exc:
        update_agent_status("Remediation Agent", "Failed")
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


def approve_remediation() -> None:
    scenario = _scenario()
    actor = current_username()
    policy = record_remediation_policy(scenario.scenario_id, human_approved=True)
    if policy.outcome.value != "PERMIT":
        raise RuntimeError(f"Policy engine did not permit remediation: {policy.reason}")

    st.session_state.remediation_policy_approved = True
    record_human_decision("approved", actor=actor)
    mark_remediating()
    update_agent_status("Remediation Agent", "Approved")
    add_agent_event(
        actor,
        f"Approved remediation for {scenario.scenario_id} in the Digital Twin sandbox only.",
        event_type="Human",
    )
    add_audit_event(
        actor=actor,
        action="Approved remediation",
        category="Human Oversight",
        details=f"scenario={scenario.scenario_id}; policy={policy.outcome.value}",
    )


def reject_remediation() -> None:
    scenario = _scenario()
    actor = current_username()
    record_human_decision("rejected", actor=actor)
    add_agent_event(
        actor,
        f"Rejected remediation for {scenario.scenario_id}. No sandbox change was applied.",
        status="Rejected",
        event_type="Human",
    )
    add_audit_event(
        actor=actor,
        action="Rejected remediation",
        status="Rejected",
        category="Human Oversight",
        details=f"scenario={scenario.scenario_id}",
    )
    reject_remediation_state()


def execute_verification() -> dict:
    scenario = _scenario()
    update_agent_status("Verification Agent", "Running")
    if not st.session_state.get("remediation_policy_approved"):
        update_agent_status("Verification Agent", "Failed")
        raise RuntimeError(
            "Verification cannot apply remediation without a recorded PERMIT "
            "decision after human approval."
        )

    mark_verifying()
    config = apply_secure_mode()
    health = get_sandbox_health()
    sync_twin_from_sandbox(health)

    add_audit_event(
        actor="Sandbox Controller",
        action="Applied approved secure sandbox profile",
        category="Remediation",
        details=(
            f"scenario={scenario.scenario_id}; version={config.get('version')}; "
            f"profile={config.get('security_profile', config.get('authorization_mode'))}"
        ),
    )

    verification = run_scenario_test(scenario.scenario_id)
    st.session_state.verification_test = verification
    passed = (
        verification["result"] == "PASS"
        and verification["observed_status"] == verification["expected_status"]
    )

    add_agent_event(
        "Verification Agent",
        (
            f"Re-ran {scenario.scenario_id}. Expected HTTP "
            f"{verification['expected_status']}; observed HTTP "
            f"{verification['observed_status']}."
        ),
        status="Completed" if passed else "Failed",
    )
    add_audit_event(
        actor="Verification Agent",
        action="Real post-remediation scenario re-executed",
        status="Success" if passed else "Failed",
        category="Verification",
        details=(
            f"scenario={scenario.scenario_id}; expected={verification['expected_status']}; "
            f"observed={verification['observed_status']}"
        ),
    )

    if not passed:
        update_agent_status("Verification Agent", "Failed")
        raise RuntimeError(
            "Verification failed: the sandbox did not produce the scenario's "
            "expected secure HTTP response."
        )

    update_agent_status("Verification Agent", "Completed")
    update_agent_status("Remediation Agent", "Applied")
    mark_secured()
    complete_run(
        verification=verification,
        final_twin_version=st.session_state.twin["version"],
    )
    add_audit_event(
        actor="Verification Agent",
        action="Remediation verified successfully",
        category="Verification",
        details=(
            f"scenario={scenario.scenario_id}; secure response="
            f"HTTP {verification['observed_status']}"
        ),
    )
    return verification
