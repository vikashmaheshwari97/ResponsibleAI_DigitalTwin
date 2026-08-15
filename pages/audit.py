import pandas as pd
import streamlit as st

from services.audit_service import get_persistent_audit_events
from services.auth_service import can_manage_governance
from services.database_service import database_health
from services.evidence_service import apply_hash_chain_to_run, verify_hash_chain
from services.repository_service import list_runs
from services.ui_service import page_header, section_header, status_chip_html


page_header(
    "Persistent Audit Trail",
    "PostgreSQL-backed audit evidence with per-run SHA-256 hash-chain verification and export.",
    icon="📋",
    eyebrow="Governance & Evidence · Audit Integrity",
)

health = database_health()
if not health["connected"]:
    st.error(f"PostgreSQL unavailable: {health['error']}")
    st.stop()

runs = list_runs(limit=200)
ids = [run.run_id for run in runs]
selected = st.selectbox("Audit scope", ["All runs"] + ids)
run_id = None if selected == "All runs" else selected
events = get_persistent_audit_events(run_id=run_id)

section_header("Audit Summary", "Persisted event categories and evidence-integrity status.")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Persistent Events", len(events))
c2.metric("Human Decisions", sum(e["Category"] == "Human Oversight" for e in events))
c3.metric("Verification Events", sum(e["Category"] == "Verification" for e in events))
c4.metric("Scope", "All runs" if run_id is None else "Single run")

if run_id:
    integrity = verify_hash_chain(run_id)
    if integrity["valid"]:
        st.markdown(
            status_chip_html(
                f"Hash chain VALID · {integrity['hashed_events']} events",
                "success",
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            status_chip_html("Hash chain requires attention", "warning"),
            unsafe_allow_html=True,
        )
        st.warning(integrity.get("reason", "Hash chain not verified"))
        if can_manage_governance():
            if st.button("Backfill / Rebuild Hash Chain", use_container_width=True):
                apply_hash_chain_to_run(run_id)
                st.rerun()
        else:
            st.caption("Admin role required to rebuild the hash chain.")

section_header("Audit Evidence", "Chronological persistent audit events for the selected scope.")
if not events:
    st.info("No persistent audit events.")
else:
    df = pd.DataFrame(events)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download audit CSV",
        data=df.to_csv(index=False).encode(),
        file_name=f"{run_id or 'all'}_persistent_audit.csv",
        mime="text/csv",
        use_container_width=True,
    )
