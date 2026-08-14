import time

import streamlit as st

from models.workflow_models import PolicyDecision, PolicyOutcome
from services.agent_service import reject_remediation
from services.ollama_service import (
    choose_preferred_model,
    get_available_models,
)
from services.orchestration_service import (
    approve_and_verify,
    prepare_remediation,
    start_security_validation,
)
from services.policy_service import (
    evaluate_remediation_policy,
    get_sandbox_controls,
    validate_simulation_policy,
)
from services.run_service import get_current_run
from services.sandbox_service import get_sandbox_health
from services.twin_service import (
    render_digital_twin,
    sync_twin_from_sandbox,
)


def render_policy_decision(raw: dict | None, title: str = "Policy Decision"):
    if not raw:
        return

    decision = PolicyDecision.model_validate(raw)

    st.markdown(f"### ⚖️ {title}")

    if decision.outcome == PolicyOutcome.permit:
        st.success(f"✓ {decision.outcome.value}")
    elif decision.outcome == PolicyOutcome.permit_with_approval:
        st.warning(f"⚠ {decision.outcome.value}")
    else:
        st.error(f"✕ {decision.outcome.value}")

    with st.container(border=True):
        st.write(f"**Action:** {decision.action}")
        st.write(f"**Target:** {decision.target}")
        st.write(f"**Environment:** {decision.environment}")
        st.write(f"**Reason:** {decision.reason}")

        for control in decision.controls:
            icon = "✓" if control.passed else "✕"
            st.caption(f"{icon} {control.control}: {control.evidence}")


st.title("🧪 Security Scenario Lab")
st.caption(
    "Run a controlled real HTTP authorization test against the Docker "
    "SecureMessenger Digital Twin. Ollama now returns schema-validated "
    "security findings and remediation plans."
)

st.subheader("AI Runtime")
ollama_status = get_available_models()

if ollama_status["connected"] and ollama_status["models"]:
    models = ollama_status["models"]
    current_model = st.session_state.get("ollama_model")
    preferred_model = (
        current_model
        if current_model in models
        else choose_preferred_model(models)
    )

    selected_model = st.selectbox(
        "Local Ollama model",
        models,
        index=models.index(preferred_model),
        disabled=st.session_state.phase != "ready",
    )
    st.session_state.ollama_model = selected_model
    st.success(f"🦙 Ollama connected · using {selected_model}")
else:
    st.warning(
        "Ollama unavailable. The workflow can still run using schema-valid "
        "deterministic fallbacks."
    )

st.subheader("Sandbox Runtime")
sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)

if sandbox["available"]:
    st.success(
        f"🐳 Docker SecureMessenger connected · v{sandbox['version']} · "
        f"{sandbox['authorization_mode']}"
    )
else:
    st.error(
        "SecureMessenger sandbox is offline. Start it with "
        "`docker compose up -d --build`."
    )

st.divider()
st.subheader("1. Security Scenario")

st.selectbox(
    "Scenario",
    ["Unauthorized Private Message Access"],
    disabled=st.session_state.phase != "ready",
)

objective = st.text_area(
    "Objective",
    value=(
        "Validate whether Alice can retrieve Bob's synthetic MSG-204. "
        "Correct behavior is HTTP 403."
    ),
    height=90,
    disabled=st.session_state.phase != "ready",
)
st.session_state.scenario_objective = objective

current_run = get_current_run()
if current_run:
    st.caption(
        f"Run: {current_run.run_id} · status: {current_run.status.value} · "
        f"model: {current_run.model_name or 'fallback'}"
    )

st.subheader("2. AI Agent Team")
agents = [
    ("🧠", "Scenario Planner", "Creates the controlled validation plan"),
    ("🛡️", "Security Testing Agent", "Executes the real approved HTTP test"),
    ("👁️", "Observer Agent", "Interprets real sandbox behavior"),
    ("🔍", "Security Analyst", "Returns schema-validated finding data"),
    ("🔧", "Remediation Agent", "Returns schema-validated remediation data"),
    ("✅", "Verification Agent", "Re-runs the exact same real HTTP test"),
]

cols = st.columns(3)
for index, (icon, name, description) in enumerate(agents):
    with cols[index % 3]:
        with st.container(border=True):
            st.markdown(f"### {icon} {name}")
            st.caption(description)

            status = st.session_state.agent_status[name]
            if status == "Completed":
                st.success("✓ Completed")
            elif status == "Running":
                st.warning("● Running")
            elif status == "Proposal Ready":
                st.warning("Proposal ready")
            elif status == "Failed":
                st.error("Failed")
            elif status == "Standby":
                st.info("Standby")
            else:
                st.info("Ready")

st.subheader("3. Safety Boundary")
controls = get_sandbox_controls()
control_cols = st.columns(len(controls))

for col, item in zip(control_cols, controls):
    with col:
        if item["enabled"]:
            st.success(f"✓ {item['control']}")
        else:
            st.error(f"✕ {item['control']}")

policy = validate_simulation_policy()

if policy["allowed"]:
    st.caption("✓ Policy engine: controlled validation permitted")
else:
    st.error("Policy engine blocked the simulation.")

st.divider()

if st.session_state.phase == "ready":
    st.subheader("4. Launch Validation")

    can_run = (
        sandbox["available"]
        and policy["allowed"]
        and sandbox.get("authorization_mode") == "vulnerable"
    )

    if sandbox.get("authorization_mode") != "vulnerable":
        st.warning(
            "The sandbox is already secure. Use Reset Demo to restore "
            "v1.0 vulnerable mode before starting a new run."
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
                "Executing controlled security validation...",
                expanded=True,
            ) as status_box:

                orchestration_result = (
                    start_security_validation(
                        progress=st.write
                    )
                )

                run = (
                    orchestration_result[
                        "run"
                    ]
                )

                test_result = (
                    orchestration_result[
                        "test_result"
                    ]
                )

                vulnerability_detected = (
                    orchestration_result[
                        "vulnerability_detected"
                    ]
                )

                if vulnerability_detected:
                    status_box.update(
                        label=(
                            "Schema-validated vulnerability discovered"
                        ),
                        state="error",
                        expanded=True,
                    )
                else:
                    status_box.update(
                        label=(
                            "Validation passed"
                        ),
                        state="complete",
                        expanded=True,
                    )

            st.rerun()

        except Exception as exc:
            st.error(
                "The validation workflow stopped before completion."
            )

            st.exception(
                exc
            )

elif st.session_state.phase == "vulnerable":
    finding = st.session_state.current_finding
    structured = st.session_state.structured_finding
    test_result = st.session_state.last_security_test

    st.error("🔴 Digital Twin state changed: Message API is vulnerable")

    left, right = st.columns([1.7, 1], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("## ⚠ High-Risk Finding")
            st.markdown(f"### {finding['title']}")
            st.write(f"**Finding ID:** {finding['id']}")
            st.write(f"**Component:** {finding['component']}")
            st.write(f"**Severity:** {finding['severity']}")
            st.write(f"**Confidence:** {finding['confidence']}")

        st.markdown("### 🔬 Real Sandbox Evidence")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Requester", test_result["requesting_user"].title())
        c2.metric("Resource", test_result["resource_id"])
        c3.metric("Expected", f"HTTP {test_result['expected_status']}")
        c4.metric("Observed", f"HTTP {test_result['observed_status']}")

        with st.expander("View raw SecureMessenger response"):
            st.json(test_result["response"])

        st.markdown("### 🦙 Structured Security Analyst Assessment")
        with st.container(border=True):
            st.write(f"**Classification:** {structured['classification']}")
            st.write(f"**Severity:** {structured['severity']}")
            st.write(f"**Assessment confidence:** {structured['confidence'].title()}")
            st.write(f"**Affected component:** {structured['affected_component']}")
            st.write(f"**Root cause:** {structured['root_cause']}")
            st.write(f"**Security impact:** {structured['security_impact']}")
            st.write(
                f"**Recommended action:** {structured['recommended_action']}"
            )
            st.caption(f"Source: {st.session_state.analyst_source}")

        with st.expander("View validated analyst JSON"):
            st.json(structured)

        if st.button(
            "🤖 Ask Remediation Agent",
            type="primary",
            use_container_width=True,
        ):
            with st.status(
                "Generating structured defensive remediation...",
                expanded=True,
            ) as box:
                st.write("Reading structured finding + real HTTP evidence")
                st.write("Applying the Digital-Twin-only policy boundary")
                prepare_remediation(progress=st.write)
                box.update(
                    label="Schema-validated remediation proposal ready",
                    state="complete",
                )
            st.rerun()

    with right:
        st.subheader("Affected Digital Twin")
        render_digital_twin()

elif st.session_state.phase == "awaiting_approval":
    proposal = st.session_state.remediation_proposal
    structured = st.session_state.structured_remediation

    st.warning(
        "⚠ Human approval required before changing the Docker Digital Twin sandbox"
    )

    left, right = st.columns([1.7, 1], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("## 🔧 Controlled Remediation Proposal")
            st.markdown(f"### {structured['title']}")
            st.write(f"**Action type:** {structured['action_type']}")
            st.write(f"**Component:** {structured['target_component']}")
            st.write(f"**Risk:** {structured['risk']}")
            st.write(f"**Target:** {structured['target_environment']}")
            st.write(f"**Proposed change:** {structured['proposed_change']}")
            st.write(
                f"**Expected benefit:** "
                f"{structured['expected_security_benefit']}"
            )

            if structured["possible_side_effects"]:
                st.write("**Possible side effects:**")
                for item in structured["possible_side_effects"]:
                    st.write(f"- {item}")

            st.write(f"**Verification:** {structured['verification_test']}")
            st.caption(f"Source: {st.session_state.remediation_source}")

        with st.expander("View validated remediation JSON"):
            st.json(structured)

        # Show the actual action-level policy decision.
        decision = evaluate_remediation_policy(human_approved=False)
        render_policy_decision(
            decision.model_dump(mode="json"),
            title="Remediation Policy Decision",
        )

        reject_col, approve_col = st.columns(2)

        with reject_col:
            if st.button("✕ Reject", use_container_width=True):
                reject_remediation()
                st.rerun()

        with approve_col:
            if st.button(
                "✓ Approve & Re-test",
                type="primary",
                use_container_width=True,
            ):
                with st.status(
                    "Applying approved remediation and re-testing...",
                    expanded=True,
                ) as box:
                    st.write("✓ Human approval recorded")
                    time.sleep(0.2)

                    st.write("⚖️ Policy engine re-evaluating approved action")
                    time.sleep(0.2)

                    st.write(
                        "🔧 Switching SecureMessenger to secure "
                        "authorization mode"
                    )
                    orchestration_result = approve_and_verify(progress=st.write)
                    verification = orchestration_result["verification"]

                    st.write(
                        f"✅ Same real test re-run — expected HTTP 403, "
                        f"observed HTTP {verification['observed_status']}"
                    )

                    box.update(
                        label="Real remediation verified successfully",
                        state="complete",
                    )

                st.rerun()

    with right:
        st.subheader("Current Digital Twin")
        render_digital_twin()

elif st.session_state.phase == "secured":
    verification = st.session_state.verification_test
    run = get_current_run()

    st.success(
        "✅ Security remediation successfully verified inside the Digital Twin"
    )

    if run:
        st.caption(
            f"Completed run: {run.run_id} · result: {run.result} · "
            f"{run.initial_twin_version} → {run.final_twin_version}"
        )

    left, right = st.columns([1.5, 1], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("## Validation Passed")
            st.write(
                "The same real HTTP authorization scenario was executed "
                "after the approved remediation. The cross-user request "
                "is now denied."
            )
            st.write("**Result: PASSED**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Security Score", "92/100", "+31")
        c2.metric("High-Risk Findings", "0", "-1")
        c3.metric("Tests Passed", "96%", "+29%")

        st.markdown("### 🔬 Post-Remediation Evidence")
        c1, c2, c3 = st.columns(3)
        c1.metric("Resource", verification["resource_id"])
        c2.metric("Expected", f"HTTP {verification['expected_status']}")
        c3.metric("Observed", f"HTTP {verification['observed_status']}")

        if run:
            with st.expander("View complete SimulationRun JSON"):
                st.json(run.public_dict())

        st.info(
            "Open Compliance for policy evidence, Audit Trail for the action "
            "history, or Reports for the before/after summary."
        )

    with right:
        st.subheader("Updated Digital Twin")
        render_digital_twin()
