from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from services.database_service import database_health
from services.report_service import (
    build_run_report,
    evidence_bundle_payloads,
    evidence_bundle_zip_bytes,
    evidence_manifest_bytes,
)
from services.repository_service import list_runs
from services.ui_service import page_header, section_header, status_chip_html


page_header(
    "Evidence Reports",
    "Reconstruct a complete historical run from PostgreSQL and export auditable JSON, CSV, PDF, "
    "ZIP, and SHA-256 evidence manifests.",
    icon="📊",
    eyebrow="Governance & Evidence · Reporting",
)

health = database_health()
if not health["connected"]:
    st.error(f"PostgreSQL unavailable: {health['error']}")
    st.stop()

runs = list_runs(limit=500)
if not runs:
    st.info("No persisted runs yet.")
    st.stop()

run_ids = [run.run_id for run in runs]
selected_run_id = st.selectbox(
    "Persisted run",
    run_ids,
    format_func=lambda run_id: next(
        f"{run.run_id} · {run.scenario_id} · {run.status}"
        for run in runs
        if run.run_id == run_id
    ),
)

report = build_run_report(selected_run_id)
run = report["run"]
integrity_valid = bool(report["integrity"].get("valid"))

section_header("Executive Snapshot", "Run identity, status, model, Twin transition, and evidence integrity.")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Status", run["status"])
m2.metric("Result", run.get("result") or "—")
m3.metric("Scenario", run["scenario_id"])
m4.metric("Model", run.get("model") or "fallback")
m5.metric(
    "Twin",
    f"{run['initial_twin_version']} → {run.get('final_twin_version') or '—'}",
)

st.markdown(
    status_chip_html(
        "Evidence integrity VALID" if integrity_valid else "Evidence integrity NOT VERIFIED",
        "success" if integrity_valid else "warning",
    ),
    unsafe_allow_html=True,
)
st.write(f"**Scenario:** {run['scenario']}")
st.write(f"**Objective:** {run['objective']}")
if run.get("failure_reason"):
    st.error(f"Failure reason: {run['failure_reason']}")
if run.get("abort_reason"):
    st.warning(f"Abort reason: {run['abort_reason']}")

tabs = st.tabs(
    [
        "HTTP Evidence",
        "Finding & Remediation",
        "Governance",
        "Digital Twin",
        "Timeline",
        "Export",
    ]
)

with tabs[0]:
    section_header("Before / After HTTP Evidence", "The initial and verification requests are persisted as separate evidence stages.")
    if report["security_tests"]:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Stage": item["stage"],
                        "Requester": item["requester"],
                        "Resource": item["resource"],
                        "Expected": item["expected_status"],
                        "Observed": item["observed_status"],
                        "Vulnerability": item["vulnerability_detected"],
                        "Result": item["result"],
                    }
                    for item in report["security_tests"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        for item in report["security_tests"]:
            with st.expander(f"{item['stage'].title()} raw HTTP response"):
                st.json(item)
    else:
        st.info("No HTTP evidence stored.")

with tabs[1]:
    cols = st.columns(2, gap="large")
    with cols[0]:
        section_header("Structured Finding")
        if report["findings"]:
            st.json(report["findings"][-1])
        else:
            st.info("No finding stored for this run.")
    with cols[1]:
        section_header("Remediation")
        if report["remediations"]:
            st.json(report["remediations"][-1])
        else:
            st.info("No remediation stored for this run.")

with tabs[2]:
    section_header("Policy Decisions", "Decision-level and rule-level evidence retained in PostgreSQL.")
    if report["policy_decisions"]:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Decision ID": item["decision_id"],
                        "Action": item["action"],
                        "Outcome": item["outcome"],
                        "Reason": item["reason"],
                    }
                    for item in report["policy_decisions"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No policy decisions stored.")

    section_header("Human Oversight")
    if report["human_decisions"]:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Decision": item["decision"],
                        "Actor": item["actor"],
                        "Remediation": item["remediation_id"],
                        "Time": item["created_at"],
                    }
                    for item in report["human_decisions"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No human decision stored.")

    if report.get("policy_rule_results"):
        section_header("Rule-Level Policy Evidence")
        st.dataframe(
            pd.DataFrame(report["policy_rule_results"]),
            use_container_width=True,
            hide_index=True,
        )

with tabs[3]:
    section_header("Digital Twin Before / After", "Persisted snapshots demonstrate the controlled state transition.")
    before_col, after_col = st.columns(2, gap="large")
    with before_col:
        with st.container(border=True):
            st.markdown("#### Before")
            if report["twin"]["before"]:
                st.json(report["twin"]["before"])
            else:
                st.info("No initial Twin snapshot.")
    with after_col:
        with st.container(border=True):
            st.markdown("#### After")
            if report["twin"]["after"]:
                st.json(report["twin"]["after"])
            else:
                st.info("No final Twin snapshot.")

with tabs[4]:
    section_header("Evidence Timeline", "Chronological reconstruction of agent, policy, human, test, and audit events.")
    if report["timeline"]:
        st.dataframe(
            pd.DataFrame(report["timeline"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No timeline events available.")

with tabs[5]:
    section_header("Export Evidence Bundle", "Every bundle includes SHA-256 file checksums and byte sizes.")
    payloads = evidence_bundle_payloads(report)
    json_bytes = payloads["evidence.json"]
    pdf_bytes = payloads["report.pdf"]
    timeline_bytes = payloads["timeline.csv"]
    policy_bytes = payloads["policy_rules.csv"]
    audit_bytes = payloads["audit.csv"]
    manifest_bytes = evidence_manifest_bytes(report, payloads)
    bundle_bytes = evidence_bundle_zip_bytes(report, payloads)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Download JSON Evidence",
            data=json_bytes,
            file_name=f"{selected_run_id}_evidence.json",
            mime="application/json",
            use_container_width=True,
        )
        st.download_button(
            "Download Timeline CSV",
            data=timeline_bytes,
            file_name=f"{selected_run_id}_timeline.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name=f"{selected_run_id}_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.download_button(
            "Download Policy CSV",
            data=policy_bytes,
            file_name=f"{selected_run_id}_policy.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c3:
        st.download_button(
            "Download Full ZIP Bundle",
            data=bundle_bytes,
            file_name=f"{selected_run_id}_evidence_bundle.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
        st.download_button(
            "Download SHA-256 Manifest",
            data=manifest_bytes,
            file_name=f"{selected_run_id}_manifest.json",
            mime="application/json",
            use_container_width=True,
        )
        st.download_button(
            "Download Audit CSV",
            data=audit_bytes,
            file_name=f"{selected_run_id}_audit.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander("Raw report JSON preview"):
        st.code(json.dumps(report, indent=2, default=str), language="json")
