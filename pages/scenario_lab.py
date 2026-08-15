from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from services.agent_service import reject_remediation
from services.auth_service import can_execute_scenarios, current_identity
from services.database_service import database_health
from services.ollama_service import choose_preferred_model, get_available_models
from services.orchestration_service import (
    approve_and_verify,
    prepare_remediation,
    start_security_validation,
)
from services.policy_service import validate_simulation_policy
from services.run_service import get_current_run
from services.sandbox_service import get_sandbox_health, reset_sandbox
from services.scenario_registry_service import get_scenario, list_scenarios
from services.twin_service import render_digital_twin, select_scenario, sync_twin_from_sandbox


def render_policy_decision(raw: dict | None, title: str = "Policy Decision"):
    if not raw:
        return
    with st.container(border=True):
        st.markdown(f"#### {title}")
        outcome = raw.get("outcome")
        if outcome == "PERMIT":
            st.success("PERMIT")
        elif outcome == "PERMIT_WITH_APPROVAL":
            st.warning("PERMIT_WITH_APPROVAL")
        else:
            st.error(outcome or "UNKNOWN")
        st.caption(raw.get("reason", ""))
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

st.title("🧪 Security Scenario Lab")
st.caption(
    "Approved synthetic localhost scenarios with policy enforcement, local LLM analysis, "
    "human approval and real post-remediation verification."
)

sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)
db = database_health()
ollama = get_available_models()

runtime_cols = st.columns(3)
with runtime_cols[0]:
    if ollama["connected"]:
        if not st.session_state.get("ollama_model"):
            st.session_state.ollama_model = choose_preferred_model(ollama["models"])
        st.success(f"🦙 Ollama · {st.session_state.get('ollama_model') or 'fallback'}")
    else:
        st.warning("🦙 Ollama offline · deterministic structured fallback enabled")
with runtime_cols[1]:
    if sandbox["available"]:
        st.success(
            f"🐳 SecureMessenger · v{sandbox['version']} · "
            f"{sandbox.get('security_profile') or sandbox.get('authorization_mode')}"
        )
    else:
        st.error("🐳 SecureMessenger offline")
with runtime_cols[2]:
    if db["connected"]:
        st.success("🗄️ PostgreSQL evidence store connected")
    else:
        st.error("🗄️ PostgreSQL evidence store offline")

if not sandbox["available"] or not db["connected"]:
    st.error("Docker SecureMessenger and PostgreSQL must be available before a governed run.")
    st.stop()

scenarios = list_scenarios()
scenario_ids = [scenario.scenario_id for scenario in scenarios]
current_id = st.session_state.get("selected_scenario_id", "SCN-001")
if current_id not in scenario_ids:
    current_id = "SCN-001"

st.subheader("1. Approved Controlled Scenario")
selected_id = st.selectbox(
    "Scenario",
    scenario_ids,
    index=scenario_ids.index(current_id),
    format_func=lambda scenario_id: f"{scenario_id} · {get_scenario(scenario_id).name}",
    disabled=st.session_state.phase not in {"ready"},
)
if selected_id != st.session_state.get("selected_scenario_id"):
    select_scenario(selected_id)

scenario = get_scenario(st.session_state.selected_scenario_id)

with st.container(border=True):
    st.markdown(f"### {scenario.scenario_id} · {scenario.name}")
    st.write(scenario.description)
    st.write(f"**Objective:** {scenario.objective}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Category", scenario.category)
    m2.metric("Target", scenario.affected_component.value)
    m3.metric("Expected secure HTTP", scenario.expected_status)

st.info(
    "Safety boundary: all scenarios are predefined, synthetic, localhost-only and run "
    "against the Docker SecureMessenger Digital Twin. No arbitrary URL or payload target "
    "is accepted by the UI."
)

policy_preview = validate_simulation_policy(scenario.scenario_id)
with st.expander("Governance pre-check"):
    render_policy_decision(policy_preview["decision"], "Pre-execution Policy Preview")

if st.session_state.phase == "ready":
    if (sandbox.get("security_profile") or sandbox.get("authorization_mode")) != "vulnerable":
        st.warning("Sandbox is currently secure. Reset it before demonstrating vulnerability discovery.")
        if st.button("Reset sandbox to vulnerable profile", use_container_width=True):
            reset_sandbox()
            st.rerun()

    can_run = (
        policy_preview["allowed"]
        and sandbox["available"]
        and db["connected"]
    )
    if st.button(
        "▶ Start AI Security Simulation",
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
                        label="Schema-validated vulnerability discovered",
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
    left, right = st.columns([1.4, 1], gap="large")
    with left:
        st.error(f"⚠ Finding detected · {scenario.classification}")
        result = st.session_state.last_security_test
        render_test_result(result, "Initial HTTP Evidence")

        if st.session_state.get("structured_finding"):
            st.markdown("#### Schema-Validated Finding")
            st.json(st.session_state.structured_finding)
            st.caption(f"Source: {st.session_state.get('analyst_source')}")

        if st.button("Ask Remediation Agent", type="primary", use_container_width=True):
            with st.status("Generating governed remediation proposal...", expanded=True) as box:
                prepare_remediation(progress=st.write)
                box.update(label="Remediation proposal ready", state="complete")
            st.rerun()
    with right:
        st.subheader("Current Digital Twin")
        render_digital_twin()

elif st.session_state.phase == "awaiting_approval":
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.warning("Human approval is required before any sandbox security change.")
        st.markdown("#### Controlled Remediation Proposal")
        st.json(st.session_state.structured_remediation)
        st.caption(f"Source: {st.session_state.get('remediation_source')}")
        render_policy_decision(st.session_state.policy_decision, "Remediation Policy Decision")

        reject_col, approve_col = st.columns(2)
        with reject_col:
            if st.button("✕ Reject", use_container_width=True):
                reject_remediation()
                st.rerun()
        with approve_col:
            if st.button("✓ Approve & Re-test", type="primary", use_container_width=True):
                with st.status(
                    "Applying approved remediation and re-testing...",
                    expanded=True,
                ) as box:
                    st.write("✓ Human approval will be persisted")
                    time.sleep(0.1)
                    result = approve_and_verify(progress=st.write)
                    verification = result["verification"]
                    st.write(
                        f"✅ Same scenario re-run — expected HTTP "
                        f"{verification['expected_status']}, observed HTTP "
                        f"{verification['observed_status']}"
                    )
                    box.update(
                        label="Real remediation verified successfully",
                        state="complete",
                    )
                st.rerun()
    with right:
        st.subheader("Current Digital Twin")
        render_digital_twin()

elif st.session_state.phase in {"secured", "validated"}:
    run = get_current_run()
    if st.session_state.phase == "secured":
        st.success(f"✅ {scenario.scenario_id} remediation verified successfully")
    else:
        st.success(f"✅ {scenario.scenario_id} already satisfied the secure expectation")

    metrics = st.columns(4)
    metrics[0].metric("Run", run.run_id if run else "—")
    metrics[1].metric("Status", run.status.value if run else st.session_state.phase)
    metrics[2].metric("Result", run.result if run else "PASS")
    metrics[3].metric("Twin", st.session_state.twin["version"])

    initial = st.session_state.get("last_security_test")
    verification = st.session_state.get("verification_test")
    if initial:
        render_test_result(initial, "Initial HTTP Evidence")
    if verification:
        render_test_result(verification, "Verification HTTP Evidence")

    st.subheader("Final Digital Twin")
    render_digital_twin()
    st.info("Open Run History, Analytics and Reports to inspect persisted evidence and exports.")

elif st.session_state.phase in {"remediating", "verifying"}:
    st.warning(f"Workflow state: {st.session_state.phase}. Wait for the active operation to finish.")

else:
    st.info(f"Current workflow phase: {st.session_state.phase}")

st.divider()
st.subheader("Agent State")
st.dataframe(
    pd.DataFrame(
        [
            {"Agent": agent, "Status": status}
            for agent, status in st.session_state.agent_status.items()
        ]
    ),
    use_container_width=True,
    hide_index=True,
)
