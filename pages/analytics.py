from __future__ import annotations

import pandas as pd
import streamlit as st

from services.analytics_service import collect_run_analytics
from services.database_service import database_health
from services.ui_service import page_header, section_header


page_header(
    "Professional Run Analytics",
    "Operational analytics reconstructed from persistent PostgreSQL evidence across all controlled validation runs.",
    icon="📈",
    eyebrow="Governance & Evidence · Analytics",
)

health = database_health()
if not health["connected"]:
    st.error(f"PostgreSQL unavailable: {health['error']}")
    st.stop()

analytics = collect_run_analytics(limit=1000)
total = analytics["total_runs"]
overall_pass_rate = round((analytics["pass_runs"] / total) * 100.0, 1) if total else 0.0

section_header("Operational Summary", "High-level health, verification, governance, and execution metrics.")
row1 = st.columns(5)
row1[0].metric("Total Runs", total)
row1[1].metric("PASS", analytics["pass_runs"])
row1[2].metric("FAIL", analytics["fail_runs"])
row1[3].metric("Interrupted / Aborted", analytics["interrupted_runs"])
row1[4].metric("Rejected", analytics["rejected_runs"])

row2 = st.columns(5)
row2[0].metric("Overall Pass Rate", f"{overall_pass_rate:.1f}%")
row2[1].metric("Verification Rate", f"{analytics['verification_rate']:.1f}%")
row2[2].metric("Policy Block Rate", f"{analytics['policy_block_rate']:.1f}%")
row2[3].metric("Avg Run Duration", f"{analytics['average_duration_seconds']:.1f}s")
row2[4].metric("Human Approval Rate", f"{analytics['human_approval_rate']:.1f}%")

scenario_df = pd.DataFrame(analytics["scenario_rows"])
trend_df = pd.DataFrame(analytics["trend_rows"])

tabs = st.tabs(["Scenario Performance", "Run Trend", "Human Oversight", "Data View"])

with tabs[0]:
    section_header("Per-Scenario Performance", "Comparative outcome and verification coverage by approved scenario.")
    if scenario_df.empty:
        st.info("No runs are available yet.")
    else:
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)
        chart_data = scenario_df.set_index("Scenario ID")[["Pass", "Fail", "Interrupted"]]
        st.bar_chart(chart_data)

with tabs[1]:
    section_header("Run Trend", "Daily run volume and outcome trend reconstructed from persisted timestamps.")
    if trend_df.empty:
        st.info("No trend data is available yet.")
    else:
        trend_df["Date"] = pd.to_datetime(trend_df["Date"])
        st.line_chart(trend_df.set_index("Date")[["Runs", "Pass", "Fail"]])

with tabs[2]:
    section_header("Human Oversight", "Recorded remediation approvals and rejections.")
    h1, h2, h3 = st.columns(3)
    h1.metric("Approved Remediations", analytics["human_approvals"])
    h2.metric("Rejected Remediations", analytics["human_rejections"])
    h3.metric("Approval Rate", f"{analytics['human_approval_rate']:.1f}%")
    st.info(
        "Human-approval statistics are calculated only from persisted governance decisions; "
        "they are not inferred from UI session state."
    )

with tabs[3]:
    section_header("Interpretation", "Analytics remain available after Streamlit restarts because PostgreSQL is the evidence source.")
    st.write(
        "Verification rate counts runs with a post-remediation verification test. "
        "Policy block rate counts runs containing at least one BLOCK decision."
    )
    if not scenario_df.empty:
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)
