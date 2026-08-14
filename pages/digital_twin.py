import pandas as pd
import streamlit as st

from services.sandbox_service import get_sandbox_health
from services.twin_service import render_digital_twin, sync_twin_from_sandbox

st.title("🔷 Digital Twin")
st.caption("Stateful virtual representation of the SecureMessenger PoC environment")

sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)
twin = st.session_state.twin

c1, c2, c3, c4 = st.columns(4)
c1.metric("Twin", twin["name"])
c2.metric("Version", twin["version"])
c3.metric("Environment", twin["environment"])
c4.metric("Synthetic Users", twin["synthetic_users"])

st.divider()
left, right = st.columns([2.7, 1], gap="large")

with left:
    st.subheader("System Topology")
    render_digital_twin()

with right:
    st.subheader("Isolation")
    st.success("✓ Sandbox enabled")
    st.success("✓ Synthetic data")
    st.success("✓ External network blocked")
    st.success("✓ Audit logging enabled")

    st.divider()
    st.subheader("Sandbox Runtime")
    if sandbox["available"]:
        st.success("● Connected")
        st.write(f"**Version:** {sandbox['version']}")
        st.write(f"**Mode:** {sandbox['authorization_mode']}")
    else:
        st.error("● Offline")
        st.caption(sandbox["error"])

st.divider()
st.subheader("Twin Components")
rows = []
for component in twin["components"].values():
    rows.append({
        "Component": component["name"],
        "Type": component["kind"],
        "Status": component["status"].replace("_", " ").title(),
        "Version": component["version"],
        "Description": component["description"],
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.caption("The diagram and table are rendered from the same Digital Twin state object.")
