from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from components.twin_3d import render_live_twin_3d, render_twin_replay
from services.database_service import database_health
from services.repository_service import list_runs
from services.sandbox_service import get_sandbox_health
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
    """Render app-owned HTML without Markdown interpreting indentation as code."""
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
            <div class="rai-twin-command-detail">PostgreSQL-backed Twin snapshots and replay</div>
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
            '</div>'
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


page_header(
    "Interactive Digital Twin Control Plane",
    "Explore SecureMessenger as a live 3D system, follow the governed O1–O4 validation lifecycle, "
    "and replay evidence-backed historical simulations without re-running the sandbox.",
    icon="🔷",
    eyebrow="Control Plane · Digital Twin",
    badge="Interactive 3D · O1–O4 lifecycle · Evidence replay",
    badge_tone="info",
)

sandbox = get_sandbox_health()
sync_twin_from_sandbox(sandbox)
twin = st.session_state.twin
phase = st.session_state.phase
scenario_id = st.session_state.get("selected_scenario_id")
database = database_health()

_render_command_strip(twin=twin, phase=phase, sandbox=sandbox, database=database)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Twin", twin["name"])
c2.metric("Version", twin["version"])
c3.metric("Environment", twin["environment"])
c4.metric("Synthetic Users", twin["synthetic_users"])
c5.metric("Lifecycle", phase.replace("_", " ").title())

live_tab, replay_tab, fallback_tab = st.tabs(
    ["◈ Live 3D Twin", "▶ Evidence Replay", "◇ 2D Fallback & Inventory"]
)

with live_tab:
    section_header(
        "Live 3D Digital Twin",
        "A presentation-grade interactive system view driven by the same governed state used by the simulation and evidence pipeline.",
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

    section_header(
        "Four-Operation Model",
        "A reviewer-friendly abstraction over the underlying agent workflow. The live scene highlights the active operation automatically.",
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
            ]:
                st.markdown(status_chip_html(f"✓ {label}", tone), unsafe_allow_html=True)
                st.markdown("<div style='height:.34rem'></div>", unsafe_allow_html=True)

    st.success(
        "Live mode preserves human oversight: O3 pauses for explicit approval in the Security Scenario Lab. "
        "The 3D scene reflects controlled state transitions; it does not invent or bypass them."
    )

with replay_tab:
    section_header(
        "Historical Digital Twin Replay",
        "Replay recorded Twin states without executing SecureMessenger again. Use 1× for inspection or 3×/5× for compact partner and grant-review demonstrations.",
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
        help=(
            "Persisted runs replay actual Digital Twin snapshots. The built-in demonstration is a "
            "portable fallback when the evidence database is unavailable."
        ),
    )

    bundle = None
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

        st.caption(
            "Playback timing is presentation-normalised: long human/LLM idle periods are compressed, "
            "while every frame retains its original evidence timestamp and snapshot hash when available."
        )

        st.download_button(
            "Download replay evidence bundle (.json)",
            data=replay_json(bundle),
            file_name=f"{run_info.get('run_id', 'digital-twin')}_replay.json",
            mime="application/json",
            use_container_width=True,
        )
    elif source == "Persisted PostgreSQL run":
        st.info(
            "No Twin snapshots are stored for the selected historical run. New governed runs created "
            "after the replay upgrade capture additional O1–O4 checkpoints automatically."
        )

    with st.expander("What is actually being recorded?", expanded=False):
        st.markdown(
            """
The replay is intentionally **not a screen-recorded video**. It reconstructs the simulation from
PostgreSQL evidence:

- Digital Twin snapshots and component status at governed checkpoints;
- agent activity that occurred between snapshots;
- initial and verification HTTP evidence;
- snapshot timestamps and integrity hashes.

This keeps the demonstration interactive: reviewers can rotate the Twin, inspect components and scrub
the timeline while no live security simulation is running.
"""
        )

with fallback_tab:
    section_header(
        "2D Topology Fallback",
        "The original Mermaid topology remains available as a lightweight representation of the same governed Twin state.",
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
    "state contract. The visualization is not an independent source of truth."
)
