import pandas as pd
import streamlit as st
from services.audit_service import get_persistent_audit_events
from services.auth_service import can_manage_governance
from services.database_service import database_health
from services.evidence_service import apply_hash_chain_to_run, verify_hash_chain
from services.repository_service import list_runs
st.title("📋 Persistent Audit Trail")
st.caption("PostgreSQL-backed audit evidence with SHA-256 hash-chain verification.")
health=database_health()
if not health["connected"]: st.error(f"PostgreSQL unavailable: {health['error']}"); st.stop()
runs=list_runs(limit=200); ids=[r.run_id for r in runs]
selected=st.selectbox("Audit scope",["All runs"]+ids); run_id=None if selected=="All runs" else selected
events=get_persistent_audit_events(run_id=run_id)
c1,c2,c3=st.columns(3); c1.metric("Persistent Events",len(events)); c2.metric("Human Decisions",sum(e["Category"]=="Human Oversight" for e in events)); c3.metric("Verification Events",sum(e["Category"]=="Verification" for e in events))
if run_id:
    integrity=verify_hash_chain(run_id)
    if integrity["valid"]: st.success(f"Evidence integrity VALID · {integrity['hashed_events']} hashed event(s)")
    else:
        st.warning(f"Evidence chain requires attention: {integrity.get('reason','not hashed')}")
        if can_manage_governance():
            if st.button("Backfill / Rebuild Hash Chain"):
                apply_hash_chain_to_run(run_id)
                st.rerun()
        else:
            st.caption("Admin role required to rebuild the hash chain.")
st.divider()
if not events: st.info("No persistent audit events.")
else:
    df=pd.DataFrame(events); st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("Download audit CSV",data=df.to_csv(index=False).encode(),file_name=f"{run_id or 'all'}_persistent_audit.csv",mime="text/csv")
