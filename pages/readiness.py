from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from services.phase_completion_service import completion_summary, local_phase_status
from services.readiness_service import readiness_snapshot
from services.ui_service import (
    page_header,
    render_phase_grid,
    section_header,
    status_chip_html,
    summary_grid,
)


page_header(
    "Release & Hardening Readiness",
    "Track local PoC completion, evidence recoverability, and production-style hardening without "
    "mixing those concerns with the deferred University of Tartu deployment.",
    icon="✅",
    eyebrow="Governance & Evidence · Release Engineering",
)

snapshot = readiness_snapshot()
phase_summary = completion_summary()
phase_rows = local_phase_status()

section_header("Readiness Summary", "Four concise indicators; detailed evidence is available below.")
summary_grid(
    [
        {
            "label": "Local PoC readiness",
            "value": f"{snapshot['local_score']:.1f}%",
            "detail": "Feature-complete local validation",
        },
        {
            "label": "Hardening readiness",
            "value": f"{snapshot['hardening_score']:.1f}%",
            "detail": "Production-style local controls",
        },
        {
            "label": "Local phases complete",
            "value": f"{phase_summary['local_phases_complete']}/{phase_summary['local_phases_total']}",
            "detail": "Phases 1–10 only",
        },
        {
            "label": "DB schema",
            "value": "005",
            "detail": "twin_snapshots · frozen milestone",
        },
    ]
)

if snapshot["local_blockers"]:
    st.error("Local blockers · " + ", ".join(snapshot["local_blockers"]))
else:
    st.success("Local PoC checks have no blocking failures.")

if snapshot["hardening_blockers"]:
    st.warning("Remaining hardening · " + ", ".join(snapshot["hardening_blockers"]))
else:
    st.success("Hardening checks are complete for the local production-style smoke test.")

section_header(
    "Project Phase Completion",
    "Phases 1–10 represent the local grant/demo PoC. Phase 11 remains deliberately deferred.",
)
render_phase_grid(phase_rows)

phase10 = next(row for row in phase_rows if row["Phase"] == 10)
if phase10["Progress"] != "100%":
    st.info(
        "Phase 10 remains at 99% until the latest backup is restored into a temporary database "
        "and schema/table-count parity is verified."
    )

rows = [
    {
        "Status": item["status"],
        "Category": item["category"],
        "Check": item["name"],
        "Local Required": item["local_required"],
        "Hardening Required": item["hardening_required"],
        "Detail": item["detail"],
    }
    for item in snapshot["checks"]
]
frame = pd.DataFrame(rows)
status_order = pd.CategoricalDtype(["FAIL", "WARN", "PASS"], ordered=True)
frame["Status"] = frame["Status"].astype(status_order)
frame = frame.sort_values(["Status", "Category", "Check"]).reset_index(drop=True)
frame["Status"] = frame["Status"].astype(str)

section_header("Validation Evidence", "Operational detail is grouped into tabs instead of repeated down the page.")
tabs = st.tabs(["Checks", "Local Completion", "Hardening", "Snapshot"])

with tabs[0]:
    pass_count = int((frame["Status"] == "PASS").sum())
    warn_count = int((frame["Status"] == "WARN").sum())
    fail_count = int((frame["Status"] == "FAIL").sum())

    cols = st.columns(3)
    with cols[0]:
        st.markdown(status_chip_html(f"{pass_count} PASS", "success"), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(status_chip_html(f"{warn_count} WARN", "warning"), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(status_chip_html(f"{fail_count} FAIL", "danger"), unsafe_allow_html=True)

    st.dataframe(frame, use_container_width=True, hide_index=True)

with tabs[1]:
    st.markdown("#### Local validation")
    st.code(
        "pytest -q\n"
        "python scripts/validate_local_release.py --exercise-sandbox",
        language="bash",
    )

    st.markdown("#### Backup & restore evidence")
    st.code(
        "python scripts/backup_database.py\n"
        "python scripts/verify_backup.py\n"
        "python scripts/validate_restore_backup.py",
        language="bash",
    )

    restore = phase_summary.get("restore_validation")
    if restore:
        st.markdown(status_chip_html("ISOLATED RESTORE PASS", "success"), unsafe_allow_html=True)
        with st.expander("Restore validation evidence"):
            st.json(restore)

with tabs[2]:
    st.markdown("#### Remaining local hardening")
    st.code(
        "python scripts/prepare_hardening_secrets.py\n"
        ".\\scripts\\generate_local_tls.ps1\n"
        "python scripts/validate_hardening_config.py",
        language="powershell",
    )
    st.markdown("#### Production-style smoke test")
    st.code(
        "docker compose down\n"
        "docker compose -f docker-compose.prod.yml up -d --build\n"
        "python scripts/smoke_hardened_runtime.py",
        language="bash",
    )
    st.caption("This remains a local hardening test, not University of Tartu deployment.")

with tabs[3]:
    export_snapshot = dict(snapshot)
    export_snapshot["phase_completion"] = phase_summary

    st.download_button(
        "Download readiness JSON",
        data=json.dumps(export_snapshot, indent=2, default=str).encode("utf-8"),
        file_name="responsible_ai_twin_readiness.json",
        mime="application/json",
        use_container_width=True,
    )
    with st.expander("Raw readiness JSON"):
        st.json(export_snapshot)
