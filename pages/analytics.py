from __future__ import annotations

import pandas as pd
import streamlit as st

from services.analytics_service import collect_run_analytics
from services.database_service import database_health


st.title("📈 Professional Run Analytics")
st.caption(
    "PostgreSQL-backed operational analytics across controlled Digital Twin validation runs."
)

health = database_health()
if not health["connected"]:
    st.error(f"PostgreSQL unavailable: {health['error']}")
    st.stop()

analytics = collect_run_analytics(limit=1000)

row1 = st.columns(5)
row1[0].metric("Total Runs", analytics["total_runs"])
row1[1].metric("PASS", analytics["pass_runs"])
row1[2].metric("FAIL", analytics["fail_runs"])
row1[3].metric("Interrupted/Aborted", analytics["interrupted_runs"])
row1[4].metric("Rejected", analytics["rejected_runs"])

row2 = st.columns(4)
row2[0].metric("Verification Rate", f"{analytics['verification_rate']:.1f}%")
row2[1].metric("Policy Block Rate", f"{analytics['policy_block_rate']:.1f}%")
row2[2].metric("Avg Run Duration", f"{analytics['average_duration_seconds']:.1f}s")
row2[3].metric("Human Approval Rate", f"{analytics['human_approval_rate']:.1f}%")

st.divider()
st.subheader("Human Oversight")
h1, h2 = st.columns(2)
h1.metric("Approved Remediations", analytics["human_approvals"])
h2.metric("Rejected Remediations", analytics["human_rejections"])

st.divider()
st.subheader("Per-Scenario Performance")
scenario_df = pd.DataFrame(analytics["scenario_rows"])
if scenario_df.empty:
    st.info("No runs are available yet.")
else:
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)
    st.markdown("#### Runs by Scenario")
    st.bar_chart(scenario_df.set_index("Scenario ID")[["Pass", "Fail", "Interrupted"]])

st.divider()
st.subheader("Run Trend")
trend_df = pd.DataFrame(analytics["trend_rows"])
if trend_df.empty:
    st.info("No trend data is available yet.")
else:
    trend_df["Date"] = pd.to_datetime(trend_df["Date"])
    st.line_chart(trend_df.set_index("Date")[["Runs", "Pass", "Fail"]])

st.caption(
    "Rates are calculated from persisted PostgreSQL evidence. Verification rate counts "
    "runs containing a post-remediation verification test."
)
