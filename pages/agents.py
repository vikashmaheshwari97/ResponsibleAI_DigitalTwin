import pandas as pd
import streamlit as st


st.title("🤖 Agent Activity")
st.caption("Execution state and event timeline for the PoC agent workflow")

icons = {
    "Scenario Planner": "🧠",
    "Security Testing Agent": "🛡️",
    "Observer Agent": "👁️",
    "Security Analyst": "🔍",
    "Remediation Agent": "🔧",
    "Verification Agent": "✅",
}

st.subheader("Agent Team")
cols = st.columns(3)
for index, (agent, status) in enumerate(st.session_state.agent_status.items()):
    with cols[index % 3]:
        with st.container(border=True):
            st.markdown(f"### {icons.get(agent, '🤖')} {agent}")
            if status in {"Completed", "Applied"}:
                st.success("✓ Completed")
            elif status in {"Running", "Proposal Ready"}:
                st.warning(status)
            else:
                st.info(status)

st.divider()
st.subheader("Execution Timeline")
if not st.session_state.agent_events:
    st.info("No agent activity yet. Run the Security Scenario Lab first.")
else:
    for event in reversed(st.session_state.agent_events):
        with st.container(border=True):
            icon = "👤" if event["Type"] == "Human" else "🤖"
            st.markdown(f"**{icon} {event['Time']} — {event['Agent']}**")
            st.write(event["Action"])
            st.caption(f"Status: {event['Status']}")

    with st.expander("Raw event table"):
        st.dataframe(
            pd.DataFrame(st.session_state.agent_events),
            use_container_width=True,
            hide_index=True,
        )
