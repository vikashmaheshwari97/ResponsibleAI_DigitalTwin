from __future__ import annotations

import streamlit as st

from services import initialize_session_state, reset_demo
from services.auth_service import (
    ROLE_ADMIN,
    ROLE_AUDITOR,
    ROLE_OPERATOR,
    auth_enabled,
    current_identity,
    enforce_session_timeout,
    logout,
    render_login_gate,
)
from services.database_service import database_health
from services.policy_registry_service import seed_policy_rules


st.set_page_config(
    page_title="Responsible AI Digital Twin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session_state()
enforce_session_timeout()
render_login_gate()

identity = current_identity()
role = identity.get("role") or ROLE_AUDITOR

db = database_health()
if db["connected"]:
    try:
        seed_policy_rules()
    except Exception:
        pass

st.markdown(
    """
    <style>
      .block-container {padding-top:1.6rem;padding-bottom:3rem;max-width:1500px;}
      [data-testid='stSidebar']{border-right:1px solid #e5e7eb;}
    </style>
    """,
    unsafe_allow_html=True,
)

platform_pages = [
    st.Page("pages/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("pages/digital_twin.py", title="Digital Twin", icon="🔷"),
]

validation_pages = []
if role in {ROLE_ADMIN, ROLE_OPERATOR}:
    validation_pages.extend(
        [
            st.Page("pages/scenario_lab.py", title="Security Scenario Lab", icon="🧪"),
            st.Page("pages/agents.py", title="Agent Activity", icon="🤖"),
        ]
    )

evidence_pages = [
    st.Page("pages/run_history.py", title="Run History", icon="🗃️"),
    st.Page("pages/analytics.py", title="Run Analytics", icon="📈"),
    st.Page("pages/reports.py", title="Reports", icon="📊"),
]

if role in {ROLE_ADMIN, ROLE_AUDITOR}:
    evidence_pages.extend(
        [
            st.Page("pages/compliance.py", title="Compliance", icon="⚖️"),
            st.Page("pages/audit.py", title="Audit Trail", icon="📋"),
        ]
    )

pages = {"Platform": platform_pages}
if validation_pages:
    pages["AI Validation"] = validation_pages
pages["Governance & Evidence"] = evidence_pages

navigation = st.navigation(pages)

with st.sidebar:
    st.markdown("### 🛡️ RAI Twin")
    st.caption("Digital-Twin-Driven Responsible AI Platform")
    st.divider()
    st.caption("IDENTITY")
    st.write(f"**User:** {identity.get('username')}")
    st.write(f"**Role:** {role}")
    st.write(f"**Auth:** {'enabled' if auth_enabled() else 'local development'}")
    if auth_enabled() and st.button("Sign out", use_container_width=True):
        logout()
        st.rerun()

    st.divider()
    st.caption("ENVIRONMENT")
    st.success("● SANDBOX PoC")
    st.write(f"**Twin:** {st.session_state.twin['name']}")
    st.write(f"**Version:** {st.session_state.twin['version']}")
    st.write(f"**State:** {st.session_state.phase.replace('_', ' ').title()}")
    st.write(f"**Network:** {st.session_state.twin['external_network']}")
    st.write(f"**LLM:** {st.session_state.get('ollama_model') or 'auto-select in Scenario Lab'}")
    current_db = database_health()
    st.write("**Evidence DB:** PostgreSQL ✓" if current_db["connected"] else "**Evidence DB:** offline")
    st.divider()
    if role in {ROLE_ADMIN, ROLE_OPERATOR}:
        if st.button("↻ Reset Demo", use_container_width=True):
            reset_demo()
            st.rerun()

navigation.run()
