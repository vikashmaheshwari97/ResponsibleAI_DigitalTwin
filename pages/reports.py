from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from services.database_service import database_health
from services.report_service import (
    audit_csv_bytes,
    build_run_report,
    evidence_bundle_zip_bytes,
    policy_csv_bytes,
    report_json_bytes,
    report_pdf_bytes,
    timeline_csv_bytes,
)
from services.repository_service import list_runs


st.title("📊 Enhanced Evidence Reports")
st.caption(
    "Reconstruct persistent run evidence from PostgreSQL and export JSON, CSV, PDF, or a complete ZIP bundle."
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
selected_run_id = st.selectbox("Select persisted run", run_ids)
report = build_run_report(selected_run_id)
run = report["run"]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Status", run["status"])
m2.metric("Result", run.get("result") or "—")
m3.metric("Scenario", run["scenario_id"])
m4.metric("Model", run.get("model") or "fallback")
m5.metric(
    "Twin",
    f"{run['initial_twin_version']} → {run.get('final_twin_version') or '—'}",
)

st.subheader("Executive Summary")
st.write(f"**Scenario:** {run['scenario']}")
st.write(f"**Objective:** {run['objective']}")
st.write(
    f"**Evidence integrity:** {'VALID' if report['integrity'].get('valid') else 'NOT VERIFIED'}"
)
if run.get("failure_reason"):
    st.error(f"**Failure reason:** {run['failure_reason']}")
if run.get("abort_reason"):
    st.warning(f"**Abort reason:** {run['abort_reason']}")

st.subheader("Before / After HTTP Evidence")
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
else:
    st.info("No HTTP evidence stored.")

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Structured Finding")
    if report["findings"]:
        st.json(report["findings"][-1])
    else:
        st.info("No finding stored for this run.")
with right:
    st.subheader("Remediation")
    if report["remediations"]:
        st.json(report["remediations"][-1])
    else:
        st.info("No remediation stored for this run.")

st.subheader("Policy & Human Oversight")
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

st.subheader("Evidence Timeline")
if report["timeline"]:
    st.dataframe(
        pd.DataFrame(report["timeline"]),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No timeline events available.")

st.subheader("Digital Twin Before / After")
before_col, after_col = st.columns(2)
with before_col:
    st.markdown("#### Before")
    if report["twin"]["before"]:
        st.json(report["twin"]["before"])
    else:
        st.info("No initial Twin snapshot.")
with after_col:
    st.markdown("#### After")
    if report["twin"]["after"]:
        st.json(report["twin"]["after"])
    else:
        st.info("No final Twin snapshot.")

st.divider()
st.subheader("Export Evidence")
json_bytes = report_json_bytes(report)
pdf_bytes = report_pdf_bytes(report)
timeline_bytes = timeline_csv_bytes(report)
policy_bytes = policy_csv_bytes(report)
audit_bytes = audit_csv_bytes(report)
bundle_bytes = evidence_bundle_zip_bytes(report)

c1, c2, c3 = st.columns(3)
with c1:
    st.download_button(
        "Download JSON",
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
        "Download Audit CSV",
        data=audit_bytes,
        file_name=f"{selected_run_id}_audit.csv",
        mime="text/csv",
        use_container_width=True,
    )

with st.expander("Raw report JSON preview"):
    st.code(json.dumps(report, indent=2, default=str), language="json")
