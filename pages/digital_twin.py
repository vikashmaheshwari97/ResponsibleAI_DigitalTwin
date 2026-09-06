from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from components.twin_3d import render_live_twin_3d, render_twin_replay
from services.agent_identity_service import (
    PROTOTYPE_IDENTITY_NOTE,
    list_agent_identities,
)
from services.database_service import database_health
from services.repository_service import list_runs
from services.sandbox_service import get_sandbox_health
from services.sustainability_service import (
    codecarbon_configuration,
    measurements_by_agent,
    persisted_sustainability_summary,
    session_sustainability_summary,
)
from services.twin_replay_service import (
    build_demo_replay,
    build_live_frame,
    build_persisted_replay,
    replay_json,
)
from services.twin_service import render_digital_twin, sync_twin_from_sandbox
from services.ui_service import page_header, runtime_card, section_header, status_chip_html


def _esc(value: object) -> str:
    return html.escape(str(value))


def _render_html(markup: str) -> None:
    markup = markup.strip()
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def _render_command_strip(*, twin: dict, phase: str, sandbox: dict, database: dict) -> None:
    sandbox_state = "ONLINE" if sandbox.get("available") else "OFFLINE"
    db_state = "CONNECTED" if database.get("connected") else "OFFLINE"
    phase_label = phase.replace("_", " ").title()
    _render_html(
        f"""
        <div class="rai-twin-command">
          <div class="rai-twin-command-card primary">
            <div class="rai-twin-command-kicker">Twin mission control</div>
            <div class="rai-twin-command-value">{_esc(twin['name'])} · v{_esc(twin['version'])}</div>
            <div class="rai-twin-command-detail">One governed state contract drives the live scene, validation lifecycle, evidence snapshots and historical replay.</div>
          </div>
          <div class="rai-twin-command-card">
            <div class="rai-twin-command-kicker">Lifecycle</div>
            <div class="rai-twin-command-value">{_esc(phase_label)}</div>
            <div class="rai-twin-command-detail">Current controlled workflow state</div>
          </div>
          <div class="rai-twin-command-card">
            <div class="rai-twin-command-kicker">Sandbox</div>
            <div class="rai-twin-command-value">{sandbox_state}</div>
            <div class="rai-twin-command-detail">{_esc(sandbox.get('security_profile') or sandbox.get('authorization_mode') or 'unavailable')} profile</div>
          </div>
          <div class="rai-twin-command-card">
            <div class="rai-twin-command-kicker">Evidence</div>
            <div class="rai-twin-command-value">{db_state}</div>
            <div class="rai-twin-command-detail">PostgreSQL-backed Twin snapshots, audit and replay</div>
          </div>
        </div>
        """
    )


def _render_operation_cards() -> None:
    items = [
        ("O1", "Plan", "Policy gate and Scenario Planner prepare the governed experiment.", "o1"),
        ("O2", "Detect", "Security Tester, Observer and Analyst discover and explain unsafe behaviour.", "o2"),
        ("O3", "Remediate", "Remediation Agent proposes a defensive change and waits for human approval.", "o3"),
        ("O4", "Verify", "Verification Agent re-runs the controlled test and confirms the secured Twin state.", "o4"),
    ]
    cards = "".join(
        (
            f'<div class="rai-operation-card {css_class}">'
            f'<div class="rai-operation-id">{_esc(op_id)}</div>'
            f'<div class="rai-operation-name">{_esc(name)}</div>'
            f'<div class="rai-operation-detail">{_esc(detail)}</div>'
            "</div>"
        )
        for op_id, name, detail, css_class in items
    )
    _render_html(f'<div class="rai-operation-grid">{cards}</div>')


def _render_interaction_hints() -> None:
    _render_html(
        """
        <div class="rai-twin-hint-grid">
          <div class="rai-twin-hint"><strong>Navigate</strong> · drag the scene, scroll to zoom and use Fit scene to restore the presentation camera.</div>
          <div class="rai-twin-hint"><strong>Inspect</strong> · hover or click a component to expose its role, version, state and description.</div>
          <div class="rai-twin-hint"><strong>Present</strong> · Auto-rotate creates a hands-free research or partner demonstration while replay remains evidence-backed.</div>
        </div>
        """
    )


def _render_codecarbon_summary(summary: dict, *, title: str) -> None:
    section_header(
        title,
        "Measured locally with CodeCarbon. Values reflect the configured hardware tracking mode "
        "during the governed agent execution windows.",
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Energy",
        f"{summary['energy_kwh']:.6f} kWh"
        if summary.get("measured_stages")
        else "—",
    )
    c2.metric(
        "CO₂e",
        f"{summary['emissions_g']:.4f} g"
        if summary.get("measured_stages")
        else "—",
    )
    c3.metric("Measured Stages", summary.get("measured_stages", 0))
    c4.metric(
        "Compute Window",
        f"{summary.get('duration_s', 0.0):.2f} s"
        if summary.get("measured_stages")
        else "—",
    )
    if summary.get("measured_stages"):
        st.caption(
            f"CodeCarbon OfflineEmissionsTracker · {summary.get('country_iso_code')} · "
            f"{summary.get('tracking_mode')} tracking."
        )
    else:
        st.info("No CodeCarbon measurements are available for this run yet.")


def _render_agent_registry() -> None:
    registry = list_agent_identities(st.session_state.agent_status)
    telemetry_by_agent = measurements_by_agent()

    section_header(
        "AI Agents in this Simulation",
        "Stable prototype e-Identity IDs identify the six operational agents. Sustainability values "
        "are measured by CodeCarbon during each agent stage rather than hardcoded.",
    )

    cols = st.columns(3, gap="medium")
    for index, item in enumerate(registry):
        telemetry = telemetry_by_agent.get(item["name"], {})
        measured = telemetry.get("measured_stages", 0) > 0
        with cols[index % 3]:
            with st.container(border=True):
                st.markdown(f"**{item['name']}**")
                st.caption(f"{item['operation']} · {item['role']}")
                st.markdown(f"`{item['e_identity_id']}`")
                st.markdown(
                    status_chip_html(
                        item["status"],
                        "success"
                        if item["status"] in {"Ready", "Completed", "Applied"}
                        else "warning",
                    ),
                    unsafe_allow_html=True,
                )
                e1, e2 = st.columns(2)
                e1.metric(
                    "Energy",
                    f"{telemetry.get('energy_kwh', 0.0):.6f} kWh"
                    if measured
                    else "—",
                )
                e2.metric(
                    "CO₂e",
                    f"{telemetry.get('emissions_g', 0.0):.4f} g"
                    if measured
                    else "—",
                )
                st.caption(
                    f"CodeCarbon stages: {telemetry.get('measured_stages', 0)}"
                    if measured
                    else "CodeCarbon measurement pending"
                )

    st.caption(PROTOTYPE_IDENTITY_NOTE)


page_header(
    "Interactive Digital Twin Control Plane",
    "Explore SecureMessenger as a live 3D system, follow the governed O1–O4 validation lifecycle, "
    "inspect traceable AI-agent identities, measure sustainability with CodeCarbon, and replay "
    "evidence-backed historical simulations.",
    icon="🔷",
    eyebrow="Control Plane · Digital Twin",
    badge="Interactive 3D · Agent e-Identity · CodeCarbon · Evidence replay",
    badge_tone="info",
)

sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)
twin = st.session_state.twin
phase = st.session_state.phase
scenario_id = st.session_state.get("selected_scenario_id")
database = database_health()
codecarbon = codecarbon_configuration()

_render_command_strip(twin=twin, phase=phase, sandbox=sandbox, database=database)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Twin", twin["name"])
c2.metric("Version", twin["version"])
c3.metric("Environment", twin["environment"])
c4.metric("Synthetic Users", twin["synthetic_users"])
c5.metric("Lifecycle", phase.replace("_", " ").title())

if not codecarbon["available"]:
    st.warning(
        "CodeCarbon is not currently importable. Install the updated requirements.txt to enable "
        "measured sustainability telemetry."
    )

live_tab, replay_tab, fallback_tab = st.tabs(
    ["◈ Live 3D Twin", "▶ Evidence Replay", "◇ 2D Fallback & Inventory"]
)

with live_tab:
    section_header(
        "Live 3D Digital Twin",
        "A presentation-grade interactive system view driven by the same governed state used by "
        "the simulation and evidence pipeline.",
    )

    live_frame = build_live_frame(
        twin,
        phase,
        scenario_id=scenario_id,
        message=(
            "Current governed component state. The visualization reads the same Digital Twin object "
            "used by validation, remediation and evidence capture."
        ),
    )
    render_live_twin_3d(live_frame, height=800)
    _render_interaction_hints()

    _render_agent_registry()
    _render_codecarbon_summary(
        session_sustainability_summary(),
        title="Measured Sustainability Telemetry",
    )

    section_header(
        "Four-Operation Model",
        "A reviewer-friendly abstraction over the underlying agent workflow. "
        "The live scene highlights the active operation automatically.",
    )
    _render_operation_cards()

    left, right = st.columns([1.08, 1], gap="large")
    with left:
        section_header("Runtime & Isolation", "Safety boundaries applied to the controlled research PoC.")
        if sandbox.get("available"):
            runtime_card(
                label="Sandbox Runtime",
                value=f"SecureMessenger v{sandbox.get('version')}",
                detail=(
                    f"Profile: {sandbox.get('security_profile') or sandbox.get('authorization_mode')} · "
                    "localhost-only synthetic target"
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

    with right:
        section_header("Governed Interaction", "The visual experience never bypasses the control plane.")
        with st.container(border=True):
            for label, tone in [
                ("Synthetic data only", "success"),
                ("External targets prohibited", "success"),
                ("Human approval retained", "success"),
                ("Twin snapshots persisted", "success" if database.get("connected") else "warning"),
                ("CodeCarbon enabled", "success" if codecarbon["enabled"] and codecarbon["available"] else "warning"),
            ]:
                st.markdown(status_chip_html(f"✓ {label}", tone), unsafe_allow_html=True)
                st.markdown("<div style='height:.34rem'></div>", unsafe_allow_html=True)

    st.caption(
        "CodeCarbon machine tracking estimates the local machine's energy during each agent stage. "
        "Concurrent local activity can influence the result; switch CODECARBON_TRACKING_MODE=process "
        "for stricter Python-process attribution."
    )

with replay_tab:
    section_header(
        "Historical Digital Twin Replay",
        "Replay recorded Twin states without executing SecureMessenger again. Persisted CodeCarbon "
        "measurements are recovered from the existing audit evidence for historical runs.",
    )

    persisted_runs = []
    if database.get("connected"):
        try:
            persisted_runs = list_runs(limit=100)
        except Exception:
            persisted_runs = []

    source_options = ["Built-in demonstration"]
    if persisted_runs:
        source_options.insert(0, "Persisted PostgreSQL run")

    source = st.radio(
        "Replay source",
        source_options,
        horizontal=True,
    )

    bundle = None
    replay_sustainability = None
    selected_run_id = None

    if source == "Persisted PostgreSQL run":
        terminal_first = sorted(
            persisted_runs,
            key=lambda item: (
                item.status not in {"secured", "validated"},
                -(item.started_at.timestamp() if item.started_at else 0),
            ),
        )
        selected_run_id = st.selectbox(
            "Recorded run",
            [item.run_id for item in terminal_first],
            format_func=lambda run_id: next(
                f"{item.run_id} · {item.scenario_id} · {item.status}"
                for item in terminal_first
                if item.run_id == run_id
            ),
        )
        try:
            bundle = build_persisted_replay(selected_run_id)
            replay_sustainability = persisted_sustainability_summary(selected_run_id)
            bundle["sustainability"] = replay_sustainability
        except Exception as exc:
            st.warning(f"This run cannot be replayed yet: {exc}")
    else:
        bundle = build_demo_replay()

    if bundle and bundle.get("frames"):
        run_info = bundle["run"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Run", run_info.get("run_id") or "—")
        m2.metric("Scenario", run_info.get("scenario_id") or "—")
        m3.metric("Recorded States", len(bundle["frames"]))
        m4.metric("Outcome", run_info.get("result") or run_info.get("status") or "—")

        render_twin_replay(bundle, height=820)

        if source == "Persisted PostgreSQL run" and replay_sustainability:
            _render_codecarbon_summary(
                replay_sustainability,
                title="Historical CodeCarbon Telemetry",
            )
        else:
            st.info(
                "The built-in demonstration is a visual replay template and has no fabricated "
                "CodeCarbon sustainability measurement."
            )

        st.download_button(
            "Download replay evidence bundle (.json)",
            data=replay_json(bundle),
            file_name=f"{run_info.get('run_id', 'digital-twin')}_replay.json",
            mime="application/json",
            use_container_width=True,
        )
    elif source == "Persisted PostgreSQL run":
        st.info("No Twin snapshots are stored for the selected historical run.")

    with st.expander("What is actually measured?", expanded=False):
        st.markdown(
            """
CodeCarbon runs around each operational AI-agent stage:

- Scenario Planner;
- Security Testing Agent;
- Observer Agent;
- Security Analyst;
- Remediation Agent; and
- Verification Agent.

For each stage, the platform records duration, total energy, CO₂e, CPU/GPU/RAM energy when
available, country, tracking mode and CodeCarbon version. The measurement JSON is also written
into the existing auditable evidence stream, so historical runs can recover the telemetry
without adding a new PostgreSQL migration.
"""
        )

with fallback_tab:
    section_header(
        "2D Topology Fallback",
        "The original Mermaid topology remains available as a lightweight representation of "
        "the same governed Twin state.",
    )
    with st.container(border=True):
        render_digital_twin()

    section_header("Component Inventory", "Every governed scenario maps to a concrete Digital Twin component.")
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
    "Live 3D, replay, Mermaid fallback and persisted evidence all originate from the same Digital Twin "
    "state contract. Sustainability values are measured with CodeCarbon rather than hardcoded."
)
