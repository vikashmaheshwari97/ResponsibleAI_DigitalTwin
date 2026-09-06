import pandas as pd
import streamlit as st

from services.agent_identity_service import (
    PROTOTYPE_IDENTITY_NOTE,
    PROTOTYPE_IDENTITY_SCHEME,
    list_agent_identities,
)
from services.sustainability_service import (
    codecarbon_configuration,
    get_session_measurements,
    measurements_by_agent,
    session_sustainability_summary,
)
from services.ui_service import page_header, section_header, status_chip_html, tone_for_status


def _fmt_energy(value):
    return "—" if value is None else f"{float(value):.6f} kWh"


def _fmt_co2(value):
    return "—" if value is None else f"{float(value):.4f} g"


page_header(
    "Agent Activity",
    "Operational view of the six-agent validation team, prototype e-Identity registry, "
    "CodeCarbon sustainability telemetry, execution state, and human-governed event timeline.",
    icon="🤖",
    eyebrow="Validation Studio · Agent Operations",
    badge="Traceable agents · CodeCarbon measured · Human governed",
    badge_tone="info",
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
registry = list_agent_identities(statuses)
summary = session_sustainability_summary()
by_agent = measurements_by_agent()
config = codecarbon_configuration()

completed = sum(value in {"Completed", "Applied"} for value in statuses.values())
active = sum(value in {"Running", "Proposal Ready", "Approved"} for value in statuses.values())
failed = sum(value == "Failed" for value in statuses.values())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Registered AI Agents", len(registry))
m2.metric("Measured Stages", summary["measured_stages"])
m3.metric("Measured Energy", f"{summary['energy_kwh']:.6f} kWh" if summary["measured_stages"] else "—")
m4.metric("Measured CO₂e", f"{summary['emissions_g']:.4f} g" if summary["measured_stages"] else "—")

st.caption(
    f"CodeCarbon · offline {config['country_iso_code']} · {config['tracking_mode']} tracking · "
    f"{config['measure_power_secs']} s sampling interval."
)

section_header(
    "AI Agent Identity & Sustainability Registry",
    "Each operational agent has a stable prototype e-Identity. Energy and CO₂e values below are "
    "measured by CodeCarbon during the agent stage; they are no longer hardcoded estimates.",
)

cols = st.columns(3, gap="medium")
for index, item in enumerate(registry):
    telemetry = by_agent.get(item["name"], {})
    measured = telemetry.get("measured_stages", 0) > 0

    with cols[index % 3]:
        with st.container(border=True):
            st.markdown(f"#### {icons.get(item['name'], '🤖')} {item['name']}")
            badge_col, op_col = st.columns([1, 1])
            with badge_col:
                st.markdown(
                    status_chip_html(item["status"], tone_for_status(item["status"])),
                    unsafe_allow_html=True,
                )
            with op_col:
                st.caption(item["operation"])

            st.markdown(f"**e-Identity:** `{item['e_identity_id']}`")
            st.write(f"**Role:** {item['role']}")
            st.caption(item["description"])

            e1, e2 = st.columns(2)
            e1.metric(
                "Energy",
                f"{telemetry.get('energy_kwh', 0.0):.6f} kWh" if measured else "—",
            )
            e2.metric(
                "CO₂e",
                f"{telemetry.get('emissions_g', 0.0):.4f} g" if measured else "—",
            )
            st.caption(
                f"CodeCarbon stages: {telemetry.get('measured_stages', 0)}"
                if measured
                else "CodeCarbon measurement pending"
            )

st.caption(f"{PROTOTYPE_IDENTITY_SCHEME}. {PROTOTYPE_IDENTITY_NOTE}")

with st.expander("CodeCarbon measurement details", expanded=False):
    measurements = get_session_measurements()
    if not measurements:
        st.info("No CodeCarbon measurements yet. Run a governed scenario first.")
    else:
        rows = [
            {
                "Agent": item.get("agent"),
                "Operation": item.get("operation"),
                "Status": item.get("measurement_status"),
                "Duration (s)": item.get("duration_s"),
                "Energy (kWh)": item.get("energy_kwh"),
                "CO₂e (g)": item.get("emissions_g"),
                "CPU energy": item.get("cpu_energy_kwh"),
                "GPU energy": item.get("gpu_energy_kwh"),
                "RAM energy": item.get("ram_energy_kwh"),
                "Country": item.get("country_iso_code"),
                "Tracking": item.get("tracking_mode"),
                "CodeCarbon": item.get("codecarbon_version"),
            }
            for item in measurements
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(
            "Machine tracking measures the local machine during each agent execution window. "
            "Other concurrent machine activity can influence the estimate."
        )

section_header(
    "Execution Timeline",
    "Human and agent actions in reverse chronological order. Agent names resolve against the "
    "stable e-Identity registry above.",
)

if not st.session_state.agent_events:
    st.info("No agent activity yet. Run a controlled scenario in the Security Scenario Lab.")
else:
    identity_by_name = {item["name"]: item for item in registry}

    for event in reversed(st.session_state.agent_events):
        icon = "👤" if event["Type"] == "Human" else icons.get(event["Agent"], "🤖")
        identity = identity_by_name.get(event["Agent"])

        with st.container(border=True):
            top = st.columns([4, 1])
            with top[0]:
                st.markdown(f"**{icon} {event['Agent']}**")
                if identity:
                    st.caption(
                        f"{identity['e_identity_id']} · {identity['role']} · {identity['operation']}"
                    )
                st.write(event["Action"])
            with top[1]:
                st.markdown(
                    status_chip_html(event["Status"], tone_for_status(event["Status"])),
                    unsafe_allow_html=True,
                )
                st.caption(event["Time"])

    with st.expander("Raw event table"):
        rows = []
        for event in st.session_state.agent_events:
            identity = identity_by_name.get(event["Agent"])
            rows.append(
                {
                    **event,
                    "e-Identity": identity["e_identity_id"] if identity else "Human / N/A",
                    "Role": identity["role"] if identity else "Human reviewer",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
