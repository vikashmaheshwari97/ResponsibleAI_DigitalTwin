import pandas as pd
import streamlit as st

from services.database_service import (
    database_health,
)
from services.policy_registry_service import (
    list_policy_rules,
    seed_policy_rules,
)
from services.repository_service import (
    list_policy_decisions,
    list_policy_rule_results,
    list_runs,
)
from services.sandbox_service import (
    get_sandbox_health,
)


st.title(
    "⚖️ Compliance & Governance"
)

st.caption(
    "Technical governance controls and persisted policy-rule evidence; "
    "this PoC does not make a legal AI Act/GDPR determination."
)


sandbox = get_sandbox_health()
database = database_health()


if database["connected"]:
    seed_policy_rules()


runtime_left, runtime_right = (
    st.columns(2)
)


with runtime_left:
    if sandbox["available"]:
        st.success(
            "Docker SecureMessenger · "
            f"v{sandbox['version']} · "
            f"{sandbox['authorization_mode']}"
        )
    else:
        st.error(
            "Docker SecureMessenger offline"
        )


with runtime_right:
    if database["connected"]:
        st.success(
            "PostgreSQL persistent evidence store connected"
        )
    else:
        st.error(
            "PostgreSQL evidence store offline"
        )


st.subheader(
    "Policy Rule Registry"
)


if database["connected"]:
    rules = list_policy_rules()

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
        st.info(
            "No policy rules are currently stored."
        )


st.subheader(
    "Persistent Policy Evidence"
)


decision_rows = []
rule_rows = []


if database["connected"]:
    runs = list_runs(
        limit=30
    )

    for run in runs:

        for decision in (
            list_policy_decisions(
                run.run_id
            )
        ):
            decision_rows.append(
                {
                    "Run ID": run.run_id,
                    "Decision ID": (
                        decision.decision_id
                    ),
                    "Action": decision.action,
                    "Outcome": decision.outcome,
                    "Reason": decision.reason,
                    "Time": decision.decided_at,
                }
            )

        for result in (
            list_policy_rule_results(
                run.run_id
            )
        ):
            rule_rows.append(
                {
                    "Run ID": run.run_id,
                    "Decision ID": (
                        result.decision_id
                    ),
                    "Rule ID": result.rule_id,
                    "Status": result.status,
                    "Passed": result.passed,
                    "Evidence": result.evidence,
                }
            )


if decision_rows:
    st.dataframe(
        pd.DataFrame(
            decision_rows
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(
        "No persisted policy decisions yet."
    )


if rule_rows:
    st.markdown(
        "#### Rule-level evaluation evidence"
    )

    st.dataframe(
        pd.DataFrame(
            rule_rows
        ),
        use_container_width=True,
        hide_index=True,
    )


st.subheader(
    "Responsible-AI Control Mapping"
)


mapping = pd.DataFrame(
    [
        [
            "Human oversight",
            "POL-HUM-001 + explicit approval record",
            "Demonstrated",
        ],
        [
            "Traceability",
            "Persistent PostgreSQL run/audit evidence",
            "Demonstrated",
        ],
        [
            "Data minimisation",
            "POL-DATA-001 synthetic PoC records only",
            "Demonstrated",
        ],
        [
            "Environment boundary",
            "POL-SBX-001 + POL-NET-001",
            "Demonstrated",
        ],
        [
            "Policy enforcement",
            "Rule-level PASS/PENDING/FAIL evidence",
            "Demonstrated",
        ],
        [
            "Verification",
            "POL-VER-001 + real HTTP re-test",
            "Demonstrated",
        ],
        [
            "Evidence integrity",
            "SHA-256 audit-event hash chain",
            "Demonstrated",
        ],
        [
            "Legal compliance",
            "Formal AI Act/GDPR legal assessment",
            "Not assessed by this PoC",
        ],
    ],
    columns=[
        "Area",
        "PoC evidence",
        "Status",
    ],
)


st.dataframe(
    mapping,
    use_container_width=True,
    hide_index=True,
)
