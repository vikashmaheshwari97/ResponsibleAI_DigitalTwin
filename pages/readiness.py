from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from services.readiness_service import readiness_snapshot


st.title("✅ Local Release & Hardening Readiness")
st.caption(
    "Validate the local feature-complete PoC and the deployment-hardening configuration "
    "without changing the core PostgreSQL schema. University of Tartu deployment remains deferred."
)

snapshot = readiness_snapshot()

m1, m2, m3 = st.columns(3)
m1.metric("Local PoC Readiness", f"{snapshot['local_score']:.1f}%")
m2.metric("Hardening Readiness", f"{snapshot['hardening_score']:.1f}%")
m3.metric("Expected DB Schema", snapshot["expected_alembic_version"])

if snapshot["local_blockers"]:
    st.error(
        "Local release blockers: " + ", ".join(snapshot["local_blockers"])
    )
else:
    st.success("Local feature-complete release checks have no blocking failures.")

if snapshot["hardening_blockers"]:
    st.warning(
        "Hardening is not fully validated yet. Remaining items: "
        + ", ".join(snapshot["hardening_blockers"])
    )
else:
    st.success("Local hardening checks are complete and ready for the production-style smoke test.")

st.divider()
st.subheader("Original Project Phase Status")
st.caption(
    "Engineering-completeness estimates for the local PoC. Phase 11 remains deliberately deferred."
)
st.dataframe(
    pd.DataFrame(snapshot["phase_status"]),
    use_container_width=True,
    hide_index=True,
)

st.divider()

rows = []
for item in snapshot["checks"]:
    rows.append(
        {
            "Status": item["status"],
            "Category": item["category"],
            "Check": item["name"],
            "Local Required": item["local_required"],
            "Hardening Required": item["hardening_required"],
            "Detail": item["detail"],
        }
    )

frame = pd.DataFrame(rows)
status_order = pd.CategoricalDtype(["FAIL", "WARN", "PASS"], ordered=True)
frame["Status"] = frame["Status"].astype(status_order)
frame = frame.sort_values(["Status", "Category", "Check"]).reset_index(drop=True)
frame["Status"] = frame["Status"].astype(str)

st.subheader("Readiness Checks")
st.dataframe(frame, use_container_width=True, hide_index=True)

st.divider()
left, right = st.columns(2, gap="large")

with left:
    st.subheader("Local release validation")
    st.code(
        "python scripts/validate_local_release.py\n"
        "python scripts/validate_local_release.py --exercise-sandbox",
        language="bash",
    )
    st.caption(
        "The optional sandbox exercise performs the four approved HTTP scenario contracts "
        "in vulnerable and secure profiles and restores the sandbox afterwards."
    )

with right:
    st.subheader("Hardening validation")
    st.code(
        "python scripts/prepare_hardening_secrets.py\n"
        "python scripts/verify_backup.py\n"
        "python scripts/validate_hardening_config.py\n"
        "python scripts/smoke_hardened_runtime.py",
        language="bash",
    )
    st.caption(
        "Generate local TLS material with the existing PowerShell/WSL helper before the "
        "production-style HTTPS smoke test."
    )

st.divider()
st.subheader("Readiness Snapshot")
st.download_button(
    "Download readiness JSON",
    data=json.dumps(snapshot, indent=2).encode("utf-8"),
    file_name="responsible_ai_twin_readiness.json",
    mime="application/json",
    use_container_width=True,
)

with st.expander("Raw readiness JSON"):
    st.json(snapshot)
