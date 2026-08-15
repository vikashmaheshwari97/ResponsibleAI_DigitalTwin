import pandas as pd
import streamlit as st

from services.auth_service import auth_enabled
from services.database_service import database_health
from services.policy_registry_service import list_policy_rules, seed_policy_rules
from services.repository_service import (
    list_policy_decisions,
    list_policy_rule_results,
    list_runs,
)
from services.sandbox_service import get_sandbox_health
from services.ui_service import page_header, runtime_card, section_header, status_chip_html


page_header(
    "Compliance & Governance",
    "Technical governance controls, persistent policy evidence, role boundaries, and responsible-AI "
    "control mapping for the local research PoC.",
    icon="⚖️",
    eyebrow="Governance & Evidence · Policy Control Plane",
    badge="Technical controls only · no legal compliance claim",
    badge_tone="warning",
)

sandbox = get_sandbox_health()
database = database_health()
if database["connected"]:
    seed_policy_rules()

runtime_cols = st.columns(2, gap="medium")
with runtime_cols[0]:
    runtime_card(
        label="Controlled Environment",
        value=(
            f"SecureMessenger v{sandbox.get('version')}"
            if sandbox.get("available")
            else "Sandbox offline"
        ),
        detail=(
            f"Profile: {sandbox.get('security_profile') or sandbox.get('authorization_mode')}"
            if sandbox.get("available")
            else sandbox.get("error") or "Docker runtime unavailable"
        ),
        tone="success" if sandbox.get("available") else "danger",
        icon="🐳",
    )
with runtime_cols[1]:
    runtime_card(
        label="Persistent Evidence",
        value="PostgreSQL connected" if database.get("connected") else "PostgreSQL offline",
        detail=(
            f"{database.get('database')} · {database.get('url')}"
            if database.get("connected")
            else database.get("error") or "Evidence store unavailable"
        ),
        tone="success" if database.get("connected") else "danger",
        icon="🗄️",
    )

rules = list_policy_rules() if database["connected"] else []
runs = list_runs(limit=100) if database["connected"] else []

decision_rows = []
rule_rows = []
for run in runs:
    for decision in list_policy_decisions(run.run_id):
        decision_rows.append(
            {
                "Run ID": run.run_id,
                "Scenario": run.scenario_id,
                "Decision ID": decision.decision_id,
                "Action": decision.action,
                "Outcome": decision.outcome,
                "Reason": decision.reason,
                "Time": decision.decided_at,
            }
        )
    for result in list_policy_rule_results(run.run_id):
        rule_rows.append(
            {
                "Run ID": run.run_id,
                "Decision ID": result.decision_id,
                "Rule ID": result.rule_id,
                "Status": result.status,
                "Passed": result.passed,
                "Evidence": result.evidence,
            }
        )

section_header("Governance Summary", "Current rule registry and persisted decision evidence.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Enabled Policy Rules", len(rules))
m2.metric("Policy Decisions", len(decision_rows))
m3.metric("Rule Evaluations", len(rule_rows))
m4.metric("Authentication", "Enabled" if auth_enabled() else "Local-dev")

tabs = st.tabs(["Policy Registry", "Decision Evidence", "Control Mapping"])

with tabs[0]:
    section_header("Policy Rule Registry", "Priority-ordered technical controls seeded into PostgreSQL.")
    if rules:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Rule ID": rule.rule_id,
                        "Name": rule.name,
                        "Category": rule.category,
                        "Effect": rule.effect,
                        "Priority": rule.priority,
                        "Enabled": rule.enabled,
                        "Description": rule.description,
                    }
                    for rule in rules
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No policy rules are currently stored.")

with tabs[1]:
    section_header("Persistent Policy Decisions")
    if decision_rows:
        decision_df = pd.DataFrame(decision_rows)
        st.dataframe(decision_df, use_container_width=True, hide_index=True)
        outcomes = decision_df["Outcome"].value_counts().to_dict()
        chips = st.columns(3)
        for col, label, tone in [
            (chips[0], f"PERMIT · {outcomes.get('PERMIT', 0)}", "success"),
            (chips[1], f"APPROVAL · {outcomes.get('PERMIT_WITH_APPROVAL', 0)}", "warning"),
            (chips[2], f"BLOCK · {outcomes.get('BLOCK', 0)}", "danger"),
        ]:
            with col:
                st.markdown(status_chip_html(label, tone), unsafe_allow_html=True)
    else:
        st.info("No persisted policy decisions yet.")

    if rule_rows:
        section_header("Rule-Level Evaluation Evidence")
        st.dataframe(pd.DataFrame(rule_rows), use_container_width=True, hide_index=True)

with tabs[2]:
    section_header("Responsible-AI Control Mapping", "Technical evidence demonstrated by the PoC.")
    mapping = pd.DataFrame(
        [
            ["Human oversight", "POL-HUM-001 + explicit approval record", "Demonstrated"],
            ["Traceability", "Persistent PostgreSQL run/audit evidence", "Demonstrated"],
            ["Data minimisation", "POL-DATA-001 synthetic PoC records only", "Demonstrated"],
            ["Environment boundary", "POL-SBX-001 + POL-NET-001", "Demonstrated"],
            ["Scenario governance", "POL-SCN-001 approved local registry", "Demonstrated"],
            [
                "Access control",
                "POL-RBAC-001 + Streamlit RBAC",
                "Demonstrated" if auth_enabled() else "Implemented / disabled locally",
            ],
            ["Policy enforcement", "Rule-level PASS/PENDING/FAIL evidence", "Demonstrated"],
            ["Verification", "POL-VER-001 + real HTTP re-test", "Demonstrated"],
            ["Evidence integrity", "SHA-256 audit-event hash chain", "Demonstrated"],
            ["Legal compliance", "Formal AI Act/GDPR legal assessment", "Not assessed by this PoC"],
        ],
        columns=["Area", "PoC evidence", "Status"],
    )
    st.dataframe(mapping, use_container_width=True, hide_index=True)
    st.warning(
        "This mapping demonstrates engineering controls and evidence. It does not constitute a legal "
        "determination of EU AI Act, GDPR, or other regulatory compliance."
    )
