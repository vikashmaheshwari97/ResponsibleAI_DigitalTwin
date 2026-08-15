import pandas as pd
import streamlit as st

from services.sandbox_service import get_sandbox_health
from services.twin_service import render_digital_twin, sync_twin_from_sandbox
from services.ui_service import page_header, runtime_card, section_header, status_chip_html


page_header(
    "Digital Twin Control Plane",
    "Stateful virtual representation of SecureMessenger, its components, isolation controls, "
    "runtime profile, and security-state transitions.",
    icon="🔷",
    eyebrow="Platform · Digital Twin",
)

sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)
twin = st.session_state.twin

c1, c2, c3, c4 = st.columns(4)
c1.metric("Twin", twin["name"])
c2.metric("Version", twin["version"])
c3.metric("Environment", twin["environment"])
c4.metric("Synthetic Users", twin["synthetic_users"])

left, right = st.columns([2.45, 1], gap="large")
with left:
    section_header("System Topology", "Live topology rendered directly from the Digital Twin state model.")
    with st.container(border=True):
        render_digital_twin()

with right:
    section_header("Runtime & Isolation", "Local safety boundaries applied to the controlled PoC.")
    if sandbox.get("available"):
        runtime_card(
            label="Sandbox Runtime",
            value=f"SecureMessenger v{sandbox.get('version')}",
            detail=(
                f"Profile: {sandbox.get('security_profile') or sandbox.get('authorization_mode')} · "
                "localhost-only"
            ),
            tone="success",
            icon="🐳",
        )
    else:
        runtime_card(
            label="Sandbox Runtime",
            value="Offline",
            detail=sandbox.get("error") or "SecureMessenger unavailable",
            tone="danger",
            icon="🐳",
        )

    st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)
    isolation = [
        ("Sandbox enabled", "success"),
        ("Synthetic data only", "success"),
        ("External targets prohibited", "success"),
        ("Persistent audit logging", "success"),
    ]
    with st.container(border=True):
        for label, tone in isolation:
            st.markdown(status_chip_html(f"✓ {label}", tone), unsafe_allow_html=True)
            st.markdown("<div style='height:.38rem'></div>", unsafe_allow_html=True)

section_header("Component Inventory", "Every governed scenario maps to one of these Twin components.")
components = list(twin["components"].values())
cols = st.columns(3, gap="medium")
for index, component in enumerate(components):
    with cols[index % 3]:
        status = component["status"].replace("_", " ").title()
        tone = (
            "success"
            if component["status"] in {"healthy", "secured"}
            else "danger"
            if component["status"] == "vulnerable"
            else "warning"
            if component["status"] == "testing"
            else "neutral"
        )
        with st.container(border=True):
            st.markdown(f"#### {component['name']}")
            st.markdown(status_chip_html(status, tone), unsafe_allow_html=True)
            st.caption(component["description"])
            st.write(f"**Type:** {component['kind']}")
            st.write(f"**Version:** {component['version']}")

with st.expander("Detailed component table"):
    rows = [
        {
            "Component": component["name"],
            "Type": component["kind"],
            "Status": component["status"].replace("_", " ").title(),
            "Version": component["version"],
            "Description": component["description"],
        }
        for component in components
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.caption(
    "The topology, component cards, and evidence snapshots all originate from the same "
    "Digital Twin state object; the core model remains frozen at the current milestone."
)
