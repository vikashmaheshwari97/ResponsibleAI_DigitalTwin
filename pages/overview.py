import streamlit as st

from services.database_service import database_health
from services.ollama_service import get_available_models
from services.sandbox_service import get_sandbox_health
from services.twin_service import (
    get_platform_metrics,
    render_digital_twin,
    sync_twin_from_sandbox,
)
from services.ui_service import (
    page_header,
    runtime_card,
    section_header,
    simple_card,
    workflow_stepper,
)


page_header(
    "Responsible AI Digital Twin",
    "A professional control plane for safe AI-agent validation, governed remediation, "
    "persistent evidence, and auditable Digital Twin verification.",
    icon="◈",
    eyebrow="Research Platform · Local Feature-Complete PoC",
    badge="Local sandbox · Synthetic data · Human governed",
    badge_tone="success",
)

sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)
db_status = database_health()
ollama_status = get_available_models()
metrics = get_platform_metrics()

section_header("Runtime Health", "Live status of the local services supporting this Digital Twin.")
health_cols = st.columns(3, gap="medium")
with health_cols[0]:
    runtime_card(
        label="SecureMessenger",
        value=(
            f"Online · v{sandbox.get('version')}"
            if sandbox.get("available")
            else "Offline"
        ),
        detail=(
            f"Security profile: {sandbox.get('security_profile') or sandbox.get('authorization_mode')}"
            if sandbox.get("available")
            else sandbox.get("error") or "Docker sandbox unavailable"
        ),
        tone="success" if sandbox.get("available") else "danger",
        icon="🐳",
    )
with health_cols[1]:
    runtime_card(
        label="Evidence Store",
        value="PostgreSQL online" if db_status.get("connected") else "PostgreSQL offline",
        detail=(
            f"{db_status.get('database')} · {db_status.get('url')}"
            if db_status.get("connected")
            else db_status.get("error") or "Connection unavailable"
        ),
        tone="success" if db_status.get("connected") else "danger",
        icon="🗄️",
    )
with health_cols[2]:
    runtime_card(
        label="Local AI Runtime",
        value=(
            f"Ollama · {len(ollama_status.get('models', []))} model(s)"
            if ollama_status.get("connected")
            else "Fallback-ready"
        ),
        detail=(
            ", ".join(ollama_status.get("models", [])[:3])
            if ollama_status.get("models")
            else "Deterministic schema-valid fallback is available"
        ),
        tone="success" if ollama_status.get("connected") else "warning",
        icon="🦙",
    )

section_header("Platform Snapshot", "Security posture and governed workflow state.")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Security Score", f"{metrics['security_score']}/100")
c2.metric("Active Agents", metrics["active_agents"])
c3.metric("High-Risk Findings", metrics["high_findings"])
c4.metric(
    "Security Tests Passed",
    "—" if metrics["tests_passed"] is None else f"{metrics['tests_passed']}%",
)

section_header("Validation Lifecycle", "Current position in the controlled remediation workflow.")
workflow_stepper(st.session_state.phase)

left, right = st.columns([2.25, 1], gap="large")
with left:
    section_header(
        "Live Digital Twin",
        "Topology is generated from the same state object used by the governed workflow.",
    )
    with st.container(border=True):
        render_digital_twin()

with right:
    section_header("Twin State", "Current application and isolation context.")
    phase = st.session_state.phase
    if phase in {"secured", "validated"}:
        st.success("Validation complete · secure behavior verified")
    elif phase in {"vulnerable", "awaiting_approval"}:
        st.error("High-risk finding · governed action required")
    elif phase in {"running", "remediating", "verifying"}:
        st.warning(f"Workflow active · {phase.replace('_', ' ').title()}")
    else:
        st.info("Ready for a controlled validation run")

    with st.container(border=True):
        st.write(f"**Twin:** {st.session_state.twin['name']}")
        st.write(f"**Version:** {st.session_state.twin['version']}")
        st.write(f"**Environment:** {st.session_state.twin['environment']}")
        st.write(f"**Synthetic users:** {st.session_state.twin['synthetic_users']}")
        st.write(f"**External network:** {st.session_state.twin['external_network']}")

section_header("Responsible-AI Platform Layers", "The PoC is organised around four complementary control layers.")
cols = st.columns(4, gap="medium")
items = [
    ("Compliance & Governance", "Policy rules, RBAC, human oversight, audit integrity, and traceability.", "⚖️"),
    ("Controlled Compute", "Docker isolation, localhost-only services, network controls, and resource boundaries.", "🖥️"),
    ("AI Lifecycle", "Planner, tester, observer, analyst, remediation, and verification agents.", "🤖"),
    ("Digital Twin", "Stateful application model, snapshots, simulation, before/after verification, and evidence.", "🔷"),
]
for col, (title, body, icon) in zip(cols, items):
    with col:
        simple_card(title, body, icon=icon)

st.caption(
    "University of Tartu server deployment remains deliberately deferred. "
    "This console represents the local grant/demo PoC."
)
