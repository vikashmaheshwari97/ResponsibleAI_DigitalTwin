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
from services.sandbox_service import get_sandbox_health
from services.ui_service import inject_global_styles, status_chip_html, tone_for_status


st.set_page_config(
    page_title="Responsible AI Digital Twin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_styles()
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
    st.Page("pages/readiness.py", title="Release Readiness", icon="✅"),
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

sandbox = get_sandbox_health()
phase = st.session_state.phase
phase_label = phase.replace("_", " ").title()

with st.sidebar:
    st.markdown(
        """
        <div class="rai-sidebar-brand">
          <strong>🛡️ RAI Twin</strong>
          <span>Responsible AI validation & evidence console</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Keep the sidebar intentionally compact. Runtime detail belongs on Overview,
    # preventing the same information from being repeated on every page.
    st.caption("SESSION")
    st.markdown(
        f"""
        <div class="rai-sidebar-line">
          <div class="rai-sidebar-label">Identity</div>
          <div class="rai-sidebar-value">{identity.get("username") or "anonymous"} · {role}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if auth_enabled() and st.button("Sign out", use_container_width=True):
        logout()
        st.rerun()

    st.caption("CURRENT TWIN")
    st.markdown(
        f"""
        <div class="rai-sidebar-line">
          <div class="rai-sidebar-label">SecureMessenger</div>
          <div class="rai-sidebar-value">v{st.session_state.twin["version"]} · {phase_label}</div>
          <div style="margin-top:.35rem">
            {status_chip_html(
                "Sandbox online" if sandbox.get("available") else "Sandbox offline",
                "success" if sandbox.get("available") else "danger",
            )}
            {status_chip_html(
                "DB online" if db.get("connected") else "DB offline",
                "success" if db.get("connected") else "danger",
            )}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if role in {ROLE_ADMIN, ROLE_OPERATOR}:
        if st.button("↻ Reset Demo", use_container_width=True):
            reset_demo()
            st.rerun()

    st.caption("Local research PoC · Phase 11 deferred")

navigation.run()
