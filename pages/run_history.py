from __future__ import annotations

import pandas as pd
import streamlit as st

from services.analytics_service import duration_seconds
from services.auth_service import can_execute_scenarios, can_manage_governance
from services.database_service import database_health
from services.evidence_service import apply_hash_chain_to_run, verify_hash_chain
from services.repository_service import (
    list_agent_events,
    list_audit_events,
    list_findings,
    list_human_decisions,
    list_policy_decisions,
    list_policy_rule_results,
    list_remediations,
    list_runs,
    list_security_tests,
    list_twin_snapshots,
)
from services.run_service import abort_persisted_run, interrupt_persisted_run


TERMINAL = {"secured", "validated", "failed", "rejected", "interrupted", "aborted"}

st.title("🗃️ Persistent Run History")
st.caption("PostgreSQL-backed lifecycle, policy, Twin snapshots and audit-integrity evidence.")
health = database_health()
if not health["connected"]:
    st.error(f"PostgreSQL unavailable: {health['error']}")
    st.stop()
st.success(f"PostgreSQL connected · {health['database']} · {health['url']}")

runs = list_runs(limit=500)
if not runs:
    st.info("No persisted runs yet.")
    st.stop()

st.subheader("Validation Runs")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Run ID": run.run_id,
                "Scenario ID": run.scenario_id,
                "Scenario": run.scenario_name,
                "Status": run.status,
                "Result": run.result or "—",
                "Model": run.model_name or "fallback",
                "Twin": (
                    f"{run.initial_twin_version} → {run.final_twin_version}"
                    if run.final_twin_version
                    else run.initial_twin_version
                ),
                "Duration (s)": (
                    round(duration_seconds(run.started_at, run.completed_at), 1)
                    if duration_seconds(run.started_at, run.completed_at) is not None
                    else None
                ),
                "Started": run.started_at,
                "Completed": run.completed_at,
            }
            for run in runs
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

selected_run_id = st.selectbox("Inspect run", [run.run_id for run in runs])
selected = next(run for run in runs if run.run_id == selected_run_id)
st.divider()
st.subheader(selected.run_id)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Scenario", selected.scenario_id)
c2.metric("Status", selected.status)
c3.metric("Result", selected.result or "—")
c4.metric("Model", selected.model_name or "fallback")
c5.metric(
    "Twin",
    (
        f"{selected.initial_twin_version} → {selected.final_twin_version}"
        if selected.final_twin_version
        else selected.initial_twin_version
    ),
)
st.write(f"**Scenario:** {selected.scenario_name}")
st.write(f"**Objective:** {selected.objective}")
if selected.failure_reason:
    st.error(f"**Failure reason:** {selected.failure_reason}")
if selected.abort_reason:
    st.warning(f"**Abort reason:** {selected.abort_reason}")

if selected.status not in TERMINAL:
    st.warning("This run is not terminal. If the application stopped mid-run, it can be marked interrupted or aborted by an execution-authorized role.")
    if can_execute_scenarios():
        a, b = st.columns(2)
        with a:
            if st.button("Mark Interrupted", use_container_width=True):
                interrupt_persisted_run(selected_run_id, "Marked interrupted from Run History.")
                st.rerun()
        with b:
            if st.button("Abort Run", use_container_width=True):
                abort_persisted_run(selected_run_id, "Explicitly aborted from Run History.")
                st.rerun()
    else:
        st.caption("Read-only role: lifecycle mutation controls are hidden.")


tests = list_security_tests(selected_run_id)
findings = list_findings(selected_run_id)
remediations = list_remediations(selected_run_id)
human = list_human_decisions(selected_run_id)
policies = list_policy_decisions(selected_run_id)
rules = list_policy_rule_results(selected_run_id)
agents = list_agent_events(selected_run_id)
audit = list_audit_events(selected_run_id)
snapshots = list_twin_snapshots(selected_run_id)

tabs = st.tabs(
    [
        "HTTP Evidence",
        "Finding",
        "Remediation",
        "Policy Rules",
        "Human",
        "Twin Snapshots",
        "Agent Timeline",
        "Audit Integrity",
    ]
)
with tabs[0]:
    if tests:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Stage": test.stage,
                        "Requester": test.requesting_user,
                        "Resource": test.resource_id,
                        "Expected": test.expected_status,
                        "Observed": test.observed_status,
                        "Access Granted": test.access_granted,
                        "Vulnerability": test.vulnerability_detected,
                        "Result": test.result,
                    }
                    for test in tests
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        for test in tests:
            with st.expander(f"{test.stage.title()} raw response"):
                st.json(test.response_json)
    else:
        st.info("No HTTP evidence stored.")
with tabs[1]:
    if findings:
        item = findings[-1]
        st.json(
            {
                "classification": item.classification,
                "severity": item.severity,
                "confidence": item.confidence_level,
                "affected_component": item.affected_component,
                "root_cause": item.root_cause,
                "security_impact": item.security_impact,
                "recommended_action": item.recommended_action,
            }
        )
    else:
        st.info("No finding stored.")
with tabs[2]:
    if remediations:
        item = remediations[-1]
        st.json(
            {
                "remediation_id": item.remediation_id,
                "title": item.title,
                "target_component": item.target_component,
                "action_type": item.action_type,
                "proposed_change": item.proposed_change,
                "risk": item.risk,
                "expected_security_benefit": item.expected_security_benefit,
                "verification_test": item.verification_test,
            }
        )
    else:
        st.info("No remediation stored.")
with tabs[3]:
    if policies:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Decision ID": item.decision_id,
                        "Action": item.action,
                        "Outcome": item.outcome,
                        "Approval Required": item.requires_human_approval,
                        "Reason": item.reason,
                        "Time": item.decided_at,
                    }
                    for item in policies
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    if rules:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Decision ID": item.decision_id,
                        "Rule ID": item.rule_id,
                        "Status": item.status,
                        "Passed": item.passed,
                        "Evidence": item.evidence,
                    }
                    for item in rules
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    if not policies and not rules:
        st.info("No policy evidence stored.")
with tabs[4]:
    if human:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Decision": item.decision,
                        "Actor": item.actor,
                        "Remediation ID": item.remediation_id,
                        "Time": item.created_at,
                    }
                    for item in human
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No human decision stored.")
with tabs[5]:
    if snapshots:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Snapshot ID": item.snapshot_id,
                        "Version": item.twin_version,
                        "Phase": item.phase,
                        "Trigger": item.trigger,
                        "State Hash": item.state_hash,
                        "Time": item.created_at,
                    }
                    for item in snapshots
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        sid = st.selectbox("View snapshot state", [item.snapshot_id for item in snapshots])
        snap = next(item for item in snapshots if item.snapshot_id == sid)
        st.json(snap.state_json)
    else:
        st.info("No Twin snapshots stored.")
with tabs[6]:
    if agents:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Time": item.created_at,
                        "Agent": item.agent,
                        "Action": item.action,
                        "Status": item.status,
                        "Type": item.event_type,
                    }
                    for item in agents
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No agent events stored.")
with tabs[7]:
    integrity = verify_hash_chain(selected_run_id)
    if integrity["valid"]:
        st.success(f"Hash chain VALID · {integrity['hashed_events']} hashed event(s)")
    else:
        st.warning(f"Hash chain requires attention · {integrity.get('reason', 'not hashed')}")
    if can_manage_governance():
        if st.button("Rebuild / Backfill Hash Chain", use_container_width=True):
            apply_hash_chain_to_run(selected_run_id)
            st.rerun()
    elif not integrity["valid"]:
        st.caption("Admin role required to rebuild the persisted hash chain.")
    if audit:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Sequence": item.sequence_number,
                        "Time": item.created_at,
                        "Actor": item.actor,
                        "Category": item.category,
                        "Action": item.action,
                        "Status": item.status,
                        "Hash": item.event_hash,
                    }
                    for item in audit
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
