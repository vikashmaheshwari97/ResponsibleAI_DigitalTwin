import pandas as pd
import streamlit as st

from services.ui_service import page_header, section_header, status_chip_html, tone_for_status


page_header(
    "Agent Activity",
    "Operational view of the six-agent validation team, execution state, and human-governed event timeline.",
    icon="🤖",
    eyebrow="AI Validation · Agent Operations",
)

icons = {
    "Scenario Planner": "🧠",
    "Security Testing Agent": "🛡️",
    "Observer Agent": "👁️",
    "Security Analyst": "🔍",
    "Remediation Agent": "🔧",
    "Verification Agent": "✅",
}

statuses = st.session_state.agent_status
completed = sum(value in {"Completed", "Applied"} for value in statuses.values())
active = sum(value in {"Running", "Proposal Ready", "Approved"} for value in statuses.values())
failed = sum(value == "Failed" for value in statuses.values())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Agent Team", len(statuses))
m2.metric("Completed", completed)
m3.metric("Active / Pending", active)
m4.metric("Failed", failed)

section_header("Agent Team", "Each card reflects the current in-memory execution state.")
cols = st.columns(3, gap="medium")
for index, (agent, status) in enumerate(statuses.items()):
    with cols[index % 3]:
        with st.container(border=True):
            st.markdown(f"#### {icons.get(agent, '🤖')} {agent}")
            st.markdown(
                status_chip_html(status, tone_for_status(status)),
                unsafe_allow_html=True,
            )
            descriptions = {
                "Scenario Planner": "Transforms an approved registry scenario into the governed execution plan.",
                "Security Testing Agent": "Executes the real localhost HTTP validation against SecureMessenger.",
                "Observer Agent": "Interprets the observed response against the secure expectation.",
                "Security Analyst": "Produces schema-validated local LLM analysis or deterministic fallback.",
                "Remediation Agent": "Proposes defensive, sandbox-only remediation requiring human approval.",
                "Verification Agent": "Re-runs the same controlled scenario after approved remediation.",
            }
            st.caption(descriptions.get(agent, ""))

section_header("Execution Timeline", "Human and agent actions in reverse chronological order.")
if not st.session_state.agent_events:
    st.info("No agent activity yet. Run a controlled scenario in the Security Scenario Lab.")
else:
    for event in reversed(st.session_state.agent_events):
        icon = "👤" if event["Type"] == "Human" else icons.get(event["Agent"], "🤖")
        with st.container(border=True):
            top = st.columns([4, 1])
            with top[0]:
                st.markdown(f"**{icon} {event['Agent']}**")
                st.write(event["Action"])
            with top[1]:
                st.markdown(
                    status_chip_html(event["Status"], tone_for_status(event["Status"])),
                    unsafe_allow_html=True,
                )
                st.caption(event["Time"])

    with st.expander("Raw event table"):
        st.dataframe(
            pd.DataFrame(st.session_state.agent_events),
            use_container_width=True,
            hide_index=True,
        )
