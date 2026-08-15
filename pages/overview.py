import streamlit as st

from services.database_service import database_health
from services.ollama_service import get_available_models
from services.sandbox_service import get_sandbox_health
from services.twin_service import get_platform_metrics, render_digital_twin, sync_twin_from_sandbox

st.title("Responsible AI Digital Twin Platform")
st.caption("Secure AI-agent validation inside an auditable Digital Twin sandbox")

sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)
metrics = get_platform_metrics()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Security Score", f"{metrics['security_score']}/100")
c2.metric("Active Agents", metrics["active_agents"])
c3.metric("High-Risk Findings", metrics["high_findings"])
c4.metric("Security Tests Passed", "—" if metrics["tests_passed"] is None else f"{metrics['tests_passed']}%")

st.divider()
left, right = st.columns([2.4, 1], gap="large")

with left:
    st.subheader("Live Digital Twin")
    st.caption("The topology is generated from the current Digital Twin state model.")
    render_digital_twin()

with right:
    st.subheader("Twin Status")
    phase = st.session_state.phase
    if phase in {"secured", "validated"}:
        st.success("✓ Validation passed")
    elif phase in {"vulnerable", "awaiting_approval"}:
        st.error("⚠ High-risk finding detected")
    elif phase == "running":
        st.warning("● Validation running")
    else:
        st.info("Ready for validation")

    with st.container(border=True):
        st.write(f"**Digital Twin:** {st.session_state.twin['name']}")
        st.write(f"**Version:** {st.session_state.twin['version']}")
        st.write(f"**Environment:** {st.session_state.twin['environment']}")
        st.write(f"**Synthetic users:** {st.session_state.twin['synthetic_users']}")
        st.write(f"**External network:** {st.session_state.twin['external_network']}")

    if sandbox["available"]:
        st.success(f"🐳 Sandbox online · v{sandbox['version']} · {sandbox['authorization_mode']}")
    else:
        st.error("🐳 Sandbox offline")

    db_status = database_health()
    if db_status["connected"]:
        st.success("🗄️ PostgreSQL evidence store online")
    else:
        st.error("🗄️ PostgreSQL evidence store offline")

    ollama_status = get_available_models()
    if ollama_status["connected"]:
        st.success(f"🦙 Ollama online · {len(ollama_status['models'])} local model(s)")
    else:
        st.warning("🦙 Ollama offline")

st.divider()
st.subheader("Platform Architecture")
cols = st.columns(4)
items = [
    ("⚖️ Compliance", "Policy controls, human oversight, traceability"),
    ("🖥️ Compute", "Docker sandbox and secure local resources"),
    ("🤖 AI Lifecycle", "Agent orchestration, analysis, monitoring"),
    ("🔷 Digital Twin", "State, simulation, validation, safe experimentation"),
]
for col, (title, text) in zip(cols, items):
    with col:
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.caption(text)
