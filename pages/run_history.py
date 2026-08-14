from __future__ import annotations
import pandas as pd
import streamlit as st
from services.database_service import database_health
from services.evidence_service import apply_hash_chain_to_run, verify_hash_chain
from services.repository_service import (
    list_agent_events, list_audit_events, list_findings, list_human_decisions,
    list_policy_decisions, list_policy_rule_results, list_remediations,
    list_runs, list_security_tests, list_twin_snapshots,
)
from services.run_service import abort_persisted_run, interrupt_persisted_run

TERMINAL = {"secured", "failed", "rejected", "interrupted", "aborted"}

st.title("🗃️ Persistent Run History")
st.caption("PostgreSQL-backed lifecycle, policy, Twin snapshots and audit-integrity evidence.")
health=database_health()
if not health["connected"]:
    st.error(f"PostgreSQL unavailable: {health['error']}"); st.stop()
st.success(f"PostgreSQL connected · {health['database']} · {health['url']}")
runs=list_runs(limit=200)
if not runs:
    st.info("No persisted runs yet."); st.stop()

st.subheader("Validation Runs")
st.dataframe(pd.DataFrame([{
    "Run ID":r.run_id,"Scenario":r.scenario_name,"Status":r.status,"Result":r.result or "—",
    "Model":r.model_name or "fallback","Twin":f"{r.initial_twin_version} → {r.final_twin_version}" if r.final_twin_version else r.initial_twin_version,
    "Started":r.started_at,"Last Transition":r.last_transition_at,"Completed":r.completed_at,
} for r in runs]),use_container_width=True,hide_index=True)
selected_run_id=st.selectbox("Inspect run",[r.run_id for r in runs])
selected=next(r for r in runs if r.run_id==selected_run_id)
st.divider(); st.subheader(selected.run_id)
c1,c2,c3,c4=st.columns(4)
c1.metric("Status",selected.status); c2.metric("Result",selected.result or "—"); c3.metric("Model",selected.model_name or "fallback"); c4.metric("Twin",f"{selected.initial_twin_version} → {selected.final_twin_version}" if selected.final_twin_version else selected.initial_twin_version)
st.write(f"**Scenario:** {selected.scenario_name}"); st.write(f"**Objective:** {selected.objective}")
if selected.failure_reason: st.error(f"**Failure reason:** {selected.failure_reason}")
if selected.abort_reason: st.warning(f"**Abort reason:** {selected.abort_reason}")
if selected.status not in TERMINAL:
    st.warning("This run is not terminal. If the application stopped mid-run, mark it interrupted or aborted.")
    a,b=st.columns(2)
    with a:
        if st.button("Mark Interrupted",use_container_width=True):
            interrupt_persisted_run(selected_run_id,"Marked interrupted from Run History."); st.rerun()
    with b:
        if st.button("Abort Run",use_container_width=True):
            abort_persisted_run(selected_run_id,"Explicitly aborted from Run History."); st.rerun()

tests=list_security_tests(selected_run_id); findings=list_findings(selected_run_id); remediations=list_remediations(selected_run_id)
human=list_human_decisions(selected_run_id); policies=list_policy_decisions(selected_run_id); rules=list_policy_rule_results(selected_run_id)
agents=list_agent_events(selected_run_id); audit=list_audit_events(selected_run_id); snapshots=list_twin_snapshots(selected_run_id)
tabs=st.tabs(["HTTP Evidence","Finding","Remediation","Policy Rules","Human","Twin Snapshots","Agent Timeline","Audit Integrity"])
with tabs[0]:
    if tests:
        st.dataframe(pd.DataFrame([{"Stage":t.stage,"Requester":t.requesting_user,"Resource":t.resource_id,"Expected":t.expected_status,"Observed":t.observed_status,"Access Granted":t.access_granted,"Vulnerability":t.vulnerability_detected,"Result":t.result} for t in tests]),use_container_width=True,hide_index=True)
        for t in tests:
            with st.expander(f"{t.stage.title()} raw response"): st.json(t.response_json)
    else: st.info("No HTTP evidence stored.")
with tabs[1]:
    if findings:
        f=findings[-1]; st.json({"classification":f.classification,"severity":f.severity,"confidence":f.confidence_level,"affected_component":f.affected_component,"root_cause":f.root_cause,"security_impact":f.security_impact,"recommended_action":f.recommended_action})
    else: st.info("No finding stored.")
with tabs[2]:
    if remediations:
        r=remediations[-1]; st.json({"remediation_id":r.remediation_id,"title":r.title,"target_component":r.target_component,"action_type":r.action_type,"proposed_change":r.proposed_change,"risk":r.risk,"expected_security_benefit":r.expected_security_benefit,"verification_test":r.verification_test})
    else: st.info("No remediation stored.")
with tabs[3]:
    if policies: st.dataframe(pd.DataFrame([{"Decision ID":p.decision_id,"Action":p.action,"Outcome":p.outcome,"Approval Required":p.requires_human_approval,"Reason":p.reason,"Time":p.decided_at} for p in policies]),use_container_width=True,hide_index=True)
    if rules: st.dataframe(pd.DataFrame([{"Decision ID":r.decision_id,"Rule ID":r.rule_id,"Status":r.status,"Passed":r.passed,"Evidence":r.evidence} for r in rules]),use_container_width=True,hide_index=True)
    if not policies and not rules: st.info("No policy evidence stored.")
with tabs[4]:
    if human: st.dataframe(pd.DataFrame([{"Decision":h.decision,"Actor":h.actor,"Remediation ID":h.remediation_id,"Time":h.created_at} for h in human]),use_container_width=True,hide_index=True)
    else: st.info("No human decision stored.")
with tabs[5]:
    if snapshots:
        st.dataframe(pd.DataFrame([{"Snapshot ID":s.snapshot_id,"Version":s.twin_version,"Phase":s.phase,"Trigger":s.trigger,"State Hash":s.state_hash,"Time":s.created_at} for s in snapshots]),use_container_width=True,hide_index=True)
        sid=st.selectbox("View snapshot state",[s.snapshot_id for s in snapshots]); snap=next(s for s in snapshots if s.snapshot_id==sid); st.json(snap.state_json)
    else: st.info("No Twin snapshots stored.")
with tabs[6]:
    if agents: st.dataframe(pd.DataFrame([{"Time":a.created_at,"Agent":a.agent,"Action":a.action,"Status":a.status,"Type":a.event_type} for a in agents]),use_container_width=True,hide_index=True)
    else: st.info("No agent events stored.")
with tabs[7]:
    integrity=verify_hash_chain(selected_run_id)
    if integrity["valid"]: st.success(f"Hash chain VALID · {integrity['hashed_events']} hashed event(s)")
    else: st.warning(f"Hash chain requires attention · {integrity.get('reason','not hashed')}")
    if st.button("Rebuild / Backfill Hash Chain",use_container_width=True): apply_hash_chain_to_run(selected_run_id); st.rerun()
    if audit: st.dataframe(pd.DataFrame([{"Sequence":a.sequence_number,"Time":a.created_at,"Actor":a.actor,"Category":a.category,"Action":a.action,"Status":a.status,"Hash":a.event_hash} for a in audit]),use_container_width=True,hide_index=True)
