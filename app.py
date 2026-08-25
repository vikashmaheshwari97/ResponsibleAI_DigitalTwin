from __future__ import annotations

import streamlit as st

from services import initialize_session_state, reset_demo
from services.auth_service import (
    ROLE_AUDITOR,
    access_profile,
    auth_enabled,
    current_identity,
    enforce_session_timeout,
    logout,
    render_login_gate,
    role_description,
    role_display_name,
)
from services.database_service import database_health
from services.policy_registry_service import seed_policy_rules
from services.sandbox_service import get_sandbox_health
from services.ui_service import inject_global_styles, status_chip_html
from services.ui_polish_service import inject_research_polish


st.set_page_config(
    page_title="Responsible AI Digital Twin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_styles()
inject_research_polish()
initialize_session_state()
enforce_session_timeout()
render_login_gate()

identity = current_identity()
role = identity.get("role") or ROLE_AUDITOR
profile = access_profile(role)

db = database_health()
if db["connected"]:
    try:
        seed_policy_rules()
    except Exception:
        pass

# Keep the information architecture simple for external reviewers while making
# the three workspaces visually distinct in the sidebar.
control_plane_pages = [
    st.Page("pages/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("pages/digital_twin.py", title="Digital Twin", icon="🔷"),
]

validation_pages = []
if profile.get("execute"):
    validation_pages.extend(
        [
            st.Page("pages/scenario_lab.py", title="Security Scenario Lab", icon="🧪"),
            st.Page("pages/agents.py", title="Agent Activity", icon="🤖"),
        ]
    )

evidence_pages = []
if profile.get("run_history"):
    evidence_pages.append(st.Page("pages/run_history.py", title="Run History", icon="🗃️"))
if profile.get("analytics"):
    evidence_pages.append(st.Page("pages/analytics.py", title="Run Analytics", icon="📈"))
if profile.get("reports"):
    evidence_pages.append(st.Page("pages/reports.py", title="Reports", icon="📊"))
if profile.get("readiness"):
    evidence_pages.append(st.Page("pages/readiness.py", title="Release Readiness", icon="✅"))
if profile.get("compliance"):
    evidence_pages.append(st.Page("pages/compliance.py", title="Compliance", icon="⚖️"))
if profile.get("audit"):
    evidence_pages.append(st.Page("pages/audit.py", title="Audit Trail", icon="📋"))

pages = {"Control Plane": control_plane_pages}
if validation_pages:
    pages["Validation Studio"] = validation_pages
if evidence_pages:
    pages["Evidence & Governance"] = evidence_pages
navigation = st.navigation(pages)

sandbox = get_sandbox_health()
phase = st.session_state.phase
phase_label = phase.replace("_", " ").title()
role_tone = "success" if profile.get("execute") else "info"

with st.sidebar:
    st.markdown(
        """
        <div class="rai-sidebar-brand rai-sidebar-brand-v3">
          <div class="rai-sidebar-brand-mark">RAI</div>
          <div class="rai-sidebar-brand-copy">
            <strong>Digital Twin</strong>
            <span>Governed AI validation platform</span>
          </div>
          <div class="rai-sidebar-live-dot" title="Research prototype online"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="rai-sidebar-context">
          <div class="rai-sidebar-context-top">
            <span class="rai-sidebar-overline">SIGNED IN</span>
            <span class="rai-sidebar-role-pill rai-sidebar-role-{role_tone}">{role_display_name(role)}</span>
          </div>
          <div class="rai-sidebar-user">{identity.get("username") or "anonymous"}</div>
          <div class="rai-sidebar-role-copy">{role_description(role)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not profile.get("execute"):
        st.caption("Preview mode · live validation controls are intentionally restricted.")

    if auth_enabled() and st.button("Sign out", use_container_width=True, key="sidebar-signout"):
        logout()
        st.rerun()

    st.markdown("<div class='rai-sidebar-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='rai-sidebar-overline rai-sidebar-overline-block'>CURRENT TWIN</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="rai-sidebar-twin-card">
          <div class="rai-sidebar-twin-head">
            <div>
              <div class="rai-sidebar-twin-name">SecureMessenger</div>
              <div class="rai-sidebar-twin-meta">Twin v{st.session_state.twin["version"]} · {phase_label}</div>
            </div>
            <div class="rai-sidebar-state-dot {'online' if sandbox.get('available') else 'offline'}"></div>
          </div>
          <div class="rai-sidebar-status-row">
            {status_chip_html(
                "Sandbox online" if sandbox.get("available") else "Sandbox offline",
                "success" if sandbox.get("available") else "danger",
            )}
            {status_chip_html(
                "Evidence online" if db.get("connected") else "Evidence offline",
                "success" if db.get("connected") else "danger",
            )}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if profile.get("execute"):
        if st.button("↻ Reset controlled demo", use_container_width=True, key="sidebar-reset"):
            reset_demo()
            st.rerun()

    st.markdown(
        """
        <div class="rai-sidebar-footer">
          <span>Research PoC</span>
          <span class="rai-sidebar-footer-sep">•</span>
          <span>synthetic data</span>
          <span class="rai-sidebar-footer-sep">•</span>
          <span>human governed</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

navigation.run()
