from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from services.agent_service import reject_remediation
from services.auth_service import can_execute_scenarios, current_identity
from services.database_service import database_health
from services.ollama_service import choose_preferred_model, get_available_models
from services.orchestration_service import approve_and_verify, prepare_remediation, start_security_validation
from services.policy_service import validate_simulation_policy
from services.run_service import get_current_run
from services.sandbox_service import get_sandbox_health, reset_sandbox
from services.scenario_registry_service import get_scenario, list_scenarios
from services.twin_service import render_digital_twin, select_scenario, sync_twin_from_sandbox
from services.ui_service import (
    detail_grid,
    page_header,
    section_header,
    service_strip,
    status_chip_html,
    workflow_stepper,
)


def render_policy_decision(raw: dict | None, title: str = "Policy Decision") -> None:
    if not raw:
        return
    outcome = raw.get("outcome") or "UNKNOWN"
    tone = "success" if outcome == "PERMIT" else "warning" if outcome == "PERMIT_WITH_APPROVAL" else "danger"

    st.markdown(f"**{title}**")
    st.markdown(status_chip_html(outcome, tone), unsafe_allow_html=True)
    if raw.get("reason"):
        st.caption(raw["reason"])

    controls = raw.get("controls", [])
    if controls:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Control": item.get("control"),
                        "Passed": item.get("passed"),
                        "Evidence": item.get("evidence"),
                    }
                    for item in controls
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_test_result(result: dict, heading: str) -> None:
    with st.container(border=True):
        st.markdown(f"#### {heading}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Expected HTTP", result.get("expected_status"))
        c2.metric("Observed HTTP", result.get("observed_status"))
        c3.metric("Result", result.get("result"))
        st.caption(result.get("request_summary", ""))
        with st.expander("Raw synthetic HTTP evidence"):
            st.json(result.get("response"))


if not can_execute_scenarios():
    identity = current_identity()
    st.error(
        f"Role '{identity.get('role')}' has read-only access. "
        "Only admin/operator roles may execute controlled scenarios."
    )
    st.stop()

page_header(
    "Security Scenario Lab",
    "Execute one approved synthetic scenario through policy validation, real localhost HTTP testing, "
    "human-governed remediation, and verification.",
    icon="🧪",
    eyebrow="AI Validation · Controlled Experiment",
    badge="Registry-only · localhost · synthetic data",
    badge_tone="success",
)

workflow_stepper(st.session_state.phase)

sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)
db = database_health()
ollama = get_available_models()

if ollama["connected"] and not st.session_state.get("ollama_model"):
    st.session_state.ollama_model = choose_preferred_model(ollama["models"])

service_strip(
    [
        {
            "label": "AI runtime",
            "icon": "🦙",
            "value": st.session_state.get("ollama_model") or "Structured fallback",
            "status": "ONLINE" if ollama["connected"] else "FALLBACK",
            "tone": "success" if ollama["connected"] else "warning",
        },
        {
            "label": "Controlled sandbox",
            "icon": "🐳",
            "value": (
                f"SecureMessenger v{sandbox.get('version')}"
                if sandbox.get("available")
                else "SecureMessenger offline"
            ),
            "status": "ONLINE" if sandbox.get("available") else "OFFLINE",
            "tone": "success" if sandbox.get("available") else "danger",
        },
        {
            "label": "Evidence store",
            "icon": "🗄️",
            "value": "PostgreSQL connected" if db.get("connected") else "PostgreSQL offline",
            "status": "ONLINE" if db.get("connected") else "OFFLINE",
            "tone": "success" if db.get("connected") else "danger",
        },
    ]
)

if not sandbox["available"] or not db["connected"]:
    st.error("SecureMessenger and PostgreSQL must be available before a governed run.")
    st.stop()

scenarios = list_scenarios()
scenario_ids = [scenario.scenario_id for scenario in scenarios]
current_id = st.session_state.get("selected_scenario_id", "SCN-001")
if current_id not in scenario_ids:
    current_id = "SCN-001"

section_header("Approved Scenario", "Choose one predefined experiment. Scenario details are shown once, in a compact summary.")

selected_id = st.selectbox(
    "Scenario",
    scenario_ids,
    index=scenario_ids.index(current_id),
    format_func=lambda scenario_id: f"{scenario_id} · {get_scenario(scenario_id).name}",
    disabled=st.session_state.phase != "ready",
    label_visibility="collapsed",
)
if selected_id != st.session_state.get("selected_scenario_id"):
    select_scenario(selected_id)

scenario = get_scenario(st.session_state.selected_scenario_id)

with st.container(border=True):
    title_col, badge_col = st.columns([5, 1])
    with title_col:
        st.markdown(f"### {scenario.scenario_id} · {scenario.name}")
        st.write(scenario.description)
        st.caption(f"Objective · {scenario.objective}")
    with badge_col:
        st.markdown(status_chip_html("APPROVED", "success"), unsafe_allow_html=True)

    detail_grid(
        [
            ("Category", scenario.category),
            ("Target", scenario.affected_component.value),
            ("Secure HTTP", str(scenario.expected_status)),
            ("Severity", scenario.severity.value.title()),
        ]
    )

st.caption(
    "Safety boundary · Only predefined scenarios are executable. Targets, identities, tokens, payloads "
    "and request bursts are synthetic and restricted to localhost SecureMessenger."
)

policy_preview = validate_simulation_policy(scenario.scenario_id)
with st.expander("Governance pre-check", expanded=True):
    render_policy_decision(policy_preview["decision"], "Pre-execution policy")

    readiness = policy_preview.get("readiness", [])
    if readiness:
        st.markdown("**Scenario readiness**")
        categories = sorted(set(c["category"] for c in readiness))
        for cat in categories:
            items = [c for c in readiness if c["category"] == cat]
            all_passed = all(i["passed"] for i in items)
            tone = "success" if all_passed else "danger"
            st.markdown(status_chip_html(f"{cat} · {'PASS' if all_passed else 'FAIL'}", tone), unsafe_allow_html=True)
            for item in items:
                icon = "✅" if item["passed"] else "❌"
                st.markdown(f"  {icon} **{item['name']}** — {item['evidence']}")
        all_ready = all(c["passed"] for c in readiness)
        if all_ready:
            st.success("All scenario-specific readiness checks passed.")
        else:
            failed_count = sum(1 for c in readiness if not c["passed"])
            st.warning(f"{failed_count} readiness check(s) failed. The scenario may not behave as expected.")

if st.session_state.phase == "ready":
    section_header("Execute Validation", "Run the real HTTP contract against the vulnerable sandbox profile.")

    if (sandbox.get("security_profile") or sandbox.get("authorization_mode")) != "vulnerable":
        st.warning("The sandbox is currently secure. Reset it before demonstrating vulnerability discovery.")
        if st.button("Reset sandbox to vulnerable profile", use_container_width=True):
            reset_sandbox()
            st.rerun()

    can_run = bool(policy_preview["allowed"] and sandbox["available"] and db["connected"])

    if not can_run:
        st.caption("The start action is unavailable until the policy, sandbox, and database gates all pass.")

    if st.button(
        "▶ Start Governed AI Validation",
        type="primary",
        use_container_width=True,
        disabled=not can_run,
    ):
        st.session_state.simulation_count += 1
        st.session_state.orchestration_error = None
        try:
            with st.status(
                f"Executing {scenario.scenario_id} controlled validation...",
                expanded=True,
            ) as status_box:
                result = start_security_validation(progress=st.write)
                if result["vulnerability_detected"]:
                    status_box.update(
                        label="Schema-validated finding discovered",
                        state="error",
                        expanded=True,
                    )
                else:
                    status_box.update(
                        label="Secure behavior already present",
                        state="complete",
                        expanded=True,
                    )
            st.rerun()
        except Exception as exc:
            st.error("The validation workflow stopped before completion.")
            st.exception(exc)

elif st.session_state.phase == "vulnerable":
    section_header("Finding & Analysis", "Review the observed HTTP evidence and schema-validated analyst result.")
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.error(f"Finding detected · {scenario.classification}")
        render_test_result(st.session_state.last_security_test, "Initial HTTP Evidence")

        if st.session_state.get("structured_finding"):
            with st.container(border=True):
                st.markdown("#### Structured Finding")
                st.json(st.session_state.structured_finding)
                st.caption(f"Source · {st.session_state.get('analyst_source')}")

        if st.button("Generate Defensive Remediation", type="primary", use_container_width=True):
            with st.status("Generating governed remediation proposal...", expanded=True) as box:
                prepare_remediation(progress=st.write)
                box.update(label="Remediation proposal ready", state="complete")
            st.rerun()

    with right:
        section_header("Current Digital Twin")
        with st.container(border=True):
            render_digital_twin()

elif st.session_state.phase == "awaiting_approval":
    section_header("Human Approval", "No security-changing sandbox action can proceed without an explicit decision.")
    left, right = st.columns([1.55, 1], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("#### Defensive Remediation Proposal")
            st.json(st.session_state.structured_remediation)
            st.caption(f"Source · {st.session_state.get('remediation_source')}")

        with st.expander("Policy decision", expanded=True):
            render_policy_decision(st.session_state.policy_decision, "Remediation policy")

        reject_col, approve_col = st.columns(2)
        with reject_col:
            if st.button("✕ Reject", use_container_width=True):
                reject_remediation()
                st.rerun()
        with approve_col:
            if st.button("✓ Approve & Re-test", type="primary", use_container_width=True):
                with st.status("Applying approved remediation and re-testing...", expanded=True) as box:
                    st.write("✓ Human approval persisted")
                    time.sleep(0.1)
                    result = approve_and_verify(progress=st.write)
                    verification = result["verification"]
                    st.write(
                        f"✓ Re-test complete · expected HTTP {verification['expected_status']}, "
                        f"observed HTTP {verification['observed_status']}"
                    )
                    box.update(label="Remediation verified", state="complete")
                st.rerun()

    with right:
        section_header("Current Digital Twin")
        with st.container(border=True):
            render_digital_twin()

elif st.session_state.phase in {"secured", "validated"}:
    run = get_current_run()
    section_header("Verified Outcome", "The final state is backed by persistent HTTP, policy, Twin, human, and audit evidence.")
    st.success(
        f"{scenario.scenario_id} "
        + ("remediation verified successfully" if st.session_state.phase == "secured" else "already satisfied the secure expectation")
    )

    detail_grid(
        [
            ("Run", run.run_id if run else "—"),
            ("Status", run.status.value if run else st.session_state.phase),
            ("Result", run.result if run else "PASS"),
            ("Twin", st.session_state.twin["version"]),
        ]
    )

    initial = st.session_state.get("last_security_test")
    verification = st.session_state.get("verification_test")
    cols = st.columns(2, gap="large")
    with cols[0]:
        if initial:
            render_test_result(initial, "Before · Initial Evidence")
    with cols[1]:
        if verification:
            render_test_result(verification, "After · Verification Evidence")

    with st.expander("Final Digital Twin", expanded=False):
        render_digital_twin()

    st.info("Persistent evidence is available in Run History and Reports.")

elif st.session_state.phase in {"remediating", "verifying"}:
    st.warning(f"Workflow active · {st.session_state.phase.replace('_', ' ').title()}")

else:
    st.info(f"Current workflow phase: {st.session_state.phase}")

# Agent cards were removed from this page to avoid duplicating the dedicated Agent Activity view.
st.caption("Detailed agent states and event chronology are available on the Agent Activity page.")
