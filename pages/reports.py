import json
import pandas as pd
import streamlit as st
from services.database_service import database_health
from services.evidence_service import verify_hash_chain
from services.repository_service import list_findings,list_human_decisions,list_policy_decisions,list_policy_rule_results,list_remediations,list_runs,list_security_tests,list_twin_snapshots
st.title("📊 Database-Backed Validation Reports")
st.caption("Reconstruct historical Responsible AI Digital Twin reports directly from PostgreSQL.")
health=database_health()
if not health["connected"]: st.error(f"PostgreSQL unavailable: {health['error']}"); st.stop()
runs=list_runs(limit=200)
if not runs: st.info("No persisted runs available."); st.stop()
rid=st.selectbox("Select historical run",[r.run_id for r in runs]); run=next(r for r in runs if r.run_id==rid)
tests=list_security_tests(rid); findings=list_findings(rid); remediations=list_remediations(rid); human=list_human_decisions(rid); policies=list_policy_decisions(rid); rules=list_policy_rule_results(rid); snapshots=list_twin_snapshots(rid); integrity=verify_hash_chain(rid)
c1,c2,c3,c4=st.columns(4); c1.metric("Status",run.status); c2.metric("Result",run.result or "—"); c3.metric("Model",run.model_name or "fallback"); c4.metric("Twin",f"{run.initial_twin_version} → {run.final_twin_version}" if run.final_twin_version else run.initial_twin_version)
st.subheader("Executive Summary"); st.write(f"**Scenario:** {run.scenario_name}"); st.write(f"**Objective:** {run.objective}"); st.write(f"**Evidence integrity:** {'VALID' if integrity['valid'] else 'NOT VERIFIED'}")
if tests:
    st.subheader("Before / After HTTP Evidence"); st.dataframe(pd.DataFrame([{"Stage":t.stage,"Requester":t.requesting_user,"Resource":t.resource_id,"Expected":t.expected_status,"Observed":t.observed_status,"Result":t.result} for t in tests]),use_container_width=True,hide_index=True)
if findings:
    f=findings[-1]; st.subheader("Structured Finding"); st.json({"classification":f.classification,"severity":f.severity,"confidence":f.confidence_level,"affected_component":f.affected_component,"root_cause":f.root_cause,"security_impact":f.security_impact,"recommended_action":f.recommended_action})
if remediations:
    r=remediations[-1]; st.subheader("Remediation"); st.json({"remediation_id":r.remediation_id,"title":r.title,"target_component":r.target_component,"proposed_change":r.proposed_change,"risk":r.risk,"verification_test":r.verification_test})
if policies:
    st.subheader("Policy Decisions"); st.dataframe(pd.DataFrame([{"Decision ID":p.decision_id,"Action":p.action,"Outcome":p.outcome,"Reason":p.reason} for p in policies]),use_container_width=True,hide_index=True)
if human:
    st.subheader("Human Oversight"); st.dataframe(pd.DataFrame([{"Decision":h.decision,"Actor":h.actor,"Remediation":h.remediation_id,"Time":h.created_at} for h in human]),use_container_width=True,hide_index=True)
payload={"run":{"run_id":run.run_id,"scenario":run.scenario_name,"status":run.status,"result":run.result,"model":run.model_name,"initial_twin_version":run.initial_twin_version,"final_twin_version":run.final_twin_version,"started_at":str(run.started_at),"completed_at":str(run.completed_at) if run.completed_at else None},"security_tests":[{"stage":t.stage,"requester":t.requesting_user,"resource":t.resource_id,"expected_status":t.expected_status,"observed_status":t.observed_status,"result":t.result,"response":t.response_json} for t in tests],"policy_decisions":[{"decision_id":p.decision_id,"action":p.action,"outcome":p.outcome,"reason":p.reason} for p in policies],"policy_rule_results":[{"decision_id":r.decision_id,"rule_id":r.rule_id,"status":r.status,"passed":r.passed,"evidence":r.evidence} for r in rules],"twin_snapshots":[{"snapshot_id":s.snapshot_id,"version":s.twin_version,"phase":s.phase,"trigger":s.trigger,"state_hash":s.state_hash} for s in snapshots],"integrity":integrity}
st.download_button("Download JSON Evidence Bundle",data=json.dumps(payload,indent=2,default=str).encode(),file_name=f"{rid}_evidence_bundle.json",mime="application/json")
