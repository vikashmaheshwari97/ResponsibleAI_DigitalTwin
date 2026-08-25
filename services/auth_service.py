from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import streamlit as st

from services.config_service import get_bool, get_int, get_secret, get_setting


ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_AUDITOR = "auditor"
ROLE_PARTNER = "partner"

ALL_ROLES = {ROLE_ADMIN, ROLE_OPERATOR, ROLE_AUDITOR, ROLE_PARTNER}
EXECUTION_ROLES = {ROLE_ADMIN, ROLE_OPERATOR}
GOVERNANCE_ROLES = {ROLE_ADMIN, ROLE_AUDITOR, ROLE_PARTNER}
INTERNAL_GOVERNANCE_ROLES = {ROLE_ADMIN, ROLE_AUDITOR}

ROLE_LABELS = {
    ROLE_ADMIN: "Admin",
    ROLE_OPERATOR: "Operator",
    ROLE_AUDITOR: "Auditor",
    ROLE_PARTNER: "Partner",
}

ROLE_DESCRIPTIONS = {
    ROLE_ADMIN: "Full platform control",
    ROLE_OPERATOR: "Live simulation execution",
    ROLE_AUDITOR: "Governance and evidence review",
    ROLE_PARTNER: "External read-only research preview",
}

# Central source of truth for application navigation and permissions.
ROLE_ACCESS = {
    ROLE_ADMIN: {
        "execute": True,
        "run_history": True,
        "analytics": True,
        "reports": True,
        "readiness": True,
        "compliance": True,
        "audit": True,
        "manage_governance": True,
    },
    ROLE_OPERATOR: {
        "execute": True,
        "run_history": True,
        "analytics": True,
        "reports": True,
        "readiness": True,
        "compliance": False,
        "audit": False,
        "manage_governance": False,
    },
    ROLE_AUDITOR: {
        "execute": False,
        "run_history": True,
        "analytics": True,
        "reports": True,
        "readiness": True,
        "compliance": True,
        "audit": True,
        "manage_governance": False,
    },
    ROLE_PARTNER: {
        "execute": False,
        "run_history": True,
        "analytics": True,
        "reports": True,
        "readiness": False,
        "compliance": True,
        "audit": False,
        "manage_governance": False,
    },
}


def auth_enabled() -> bool:
    return get_bool("AUTH_ENABLED", False)


def _configured_users() -> list[dict]:
    users: list[dict] = []
    for role, prefix in [
        (ROLE_ADMIN, "RAI_ADMIN"),
        (ROLE_OPERATOR, "RAI_OPERATOR"),
        (ROLE_AUDITOR, "RAI_AUDITOR"),
        (ROLE_PARTNER, "RAI_PARTNER"),
    ]:
        username = get_setting(f"{prefix}_USERNAME")
        password_hash = get_secret(f"{prefix}_PASSWORD_HASH")
        if username and password_hash:
            users.append(
                {
                    "username": username,
                    "password_hash": password_hash,
                    "role": role,
                }
            )
    return users


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _session_timeout() -> timedelta:
    return timedelta(minutes=get_int("AUTH_SESSION_TIMEOUT_MINUTES", 60))


def current_identity() -> dict:
    if not auth_enabled():
        return {
            "username": "local-dev",
            "role": ROLE_ADMIN,
            "authenticated": True,
            "auth_mode": "disabled-local-development",
        }

    identity = st.session_state.get("auth_identity")
    if not identity:
        return {
            "username": None,
            "role": None,
            "authenticated": False,
            "auth_mode": "password",
        }

    return dict(identity)


def is_authenticated() -> bool:
    return bool(current_identity().get("authenticated"))


def current_role() -> str | None:
    return current_identity().get("role")


def current_username() -> str:
    return current_identity().get("username") or "anonymous"


def is_partner() -> bool:
    return current_role() == ROLE_PARTNER


def role_display_name(role: str | None = None) -> str:
    value = role or current_role()
    return ROLE_LABELS.get(value, "Unknown")


def role_description(role: str | None = None) -> str:
    value = role or current_role()
    return ROLE_DESCRIPTIONS.get(value, "Restricted access")


def access_profile(role: str | None = None) -> dict:
    value = role or current_role()
    return dict(ROLE_ACCESS.get(value, {}))


def can_execute_scenarios() -> bool:
    return bool(access_profile().get("execute"))


def can_manage_governance() -> bool:
    return bool(access_profile().get("manage_governance"))


def can_view_governance() -> bool:
    profile = access_profile()
    return bool(profile.get("compliance") or profile.get("audit"))


def can_view_internal_governance() -> bool:
    """Internal readiness/audit surfaces are intentionally hidden from partners."""
    profile = access_profile()
    return bool(profile.get("readiness") or profile.get("audit"))


def can_view_reports() -> bool:
    return bool(access_profile().get("reports"))


def can_view_analytics() -> bool:
    return bool(access_profile().get("analytics"))


def enforce_session_timeout() -> None:
    if not auth_enabled() or not is_authenticated():
        return

    last_activity_raw = st.session_state.get("auth_last_activity")
    now = _utc_now()

    if last_activity_raw:
        try:
            last_activity = datetime.fromisoformat(last_activity_raw)
            if now - last_activity > _session_timeout():
                logout()
                return
        except ValueError:
            logout()
            return

    st.session_state.auth_last_activity = now.isoformat()


def verify_credentials(username: str, password: str) -> dict | None:
    username = username.strip()
    for user in _configured_users():
        if user["username"] != username:
            continue
        try:
            if bcrypt.checkpw(
                password.encode("utf-8"),
                user["password_hash"].encode("utf-8"),
            ):
                return {
                    "username": user["username"],
                    "role": user["role"],
                    "authenticated": True,
                    "auth_mode": "password",
                }
        except ValueError:
            return None
    return None


def login(username: str, password: str) -> bool:
    identity = verify_credentials(username, password)
    if not identity:
        return False

    st.session_state.auth_identity = identity
    st.session_state.auth_last_activity = _utc_now().isoformat()

    try:
        from services.audit_service import add_audit_event

        add_audit_event(
            actor=identity["username"],
            action="Authenticated to Responsible AI Digital Twin",
            category="Authentication",
            details=f"role={identity['role']}",
        )
    except Exception:
        # Login must remain available even if the evidence store is temporarily offline.
        pass

    return True


def logout() -> None:
    identity = st.session_state.get("auth_identity") or {}
    try:
        if identity.get("username"):
            from services.audit_service import add_audit_event

            add_audit_event(
                actor=identity["username"],
                action="Logged out of Responsible AI Digital Twin",
                category="Authentication",
                details=f"role={identity.get('role')}",
            )
    except Exception:
        pass

    st.session_state.pop("auth_identity", None)
    st.session_state.pop("auth_last_activity", None)


def _inject_login_styles() -> None:
    st.markdown(
        """
        <style>
        /* Login-only presentation. A successful login triggers a rerun, so these
           rules do not leak into the authenticated application shell. */
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }

        [data-testid="stHeader"] { background: transparent !important; }

        .block-container {
            max-width: 1180px !important;
            padding-top: 3.2rem !important;
            padding-bottom: 3rem !important;
        }

        .rai-login-hero {
            min-height: 485px;
            padding: 3rem 2.6rem;
            border-radius: 24px;
            border: 1px solid #dbe4ef;
            background:
                radial-gradient(circle at 12% 15%, rgba(37,99,235,.16), transparent 18rem),
                radial-gradient(circle at 85% 78%, rgba(15,118,110,.12), transparent 18rem),
                linear-gradient(145deg, #071426 0%, #0f2340 58%, #0c3341 120%);
            box-shadow: 0 22px 60px rgba(15,23,42,.16);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: hidden;
            position: relative;
        }

        .rai-login-kicker {
            display:inline-flex;
            align-items:center;
            width:max-content;
            padding:.35rem .65rem;
            border-radius:999px;
            border:1px solid rgba(191,219,254,.35);
            background:rgba(255,255,255,.07);
            color:#bfdbfe;
            font-size:.68rem;
            font-weight:780;
            letter-spacing:.09em;
            text-transform:uppercase;
        }

        .rai-login-title {
            margin-top:1.3rem;
            color:white;
            font-size:clamp(2.15rem,4vw,3.45rem);
            line-height:1.02;
            font-weight:790;
            letter-spacing:-.055em;
            max-width:720px;
        }

        .rai-login-subtitle {
            color:#cbd5e1;
            margin-top:1rem;
            max-width:640px;
            font-size:1rem;
            line-height:1.65;
        }

        .rai-login-pills {
            display:flex;
            flex-wrap:wrap;
            gap:.5rem;
            margin-top:1.5rem;
        }

        .rai-login-pill {
            padding:.38rem .62rem;
            border-radius:999px;
            font-size:.7rem;
            color:#dbeafe;
            background:rgba(255,255,255,.075);
            border:1px solid rgba(255,255,255,.12);
        }

        .rai-login-foot {
            color:#94a3b8;
            font-size:.74rem;
            margin-top:2rem;
        }

        .rai-login-panel-title {
            color:#0f172a;
            font-size:1.5rem;
            font-weight:770;
            letter-spacing:-.03em;
            margin-bottom:.25rem;
        }

        .rai-login-panel-copy {
            color:#64748b;
            font-size:.84rem;
            line-height:1.5;
            margin-bottom:1rem;
        }

        div[data-testid="stForm"] {
            border: 0 !important;
            padding: 0 !important;
        }

        @media (max-width: 900px) {
            .rai-login-hero { min-height: 350px; padding: 2rem 1.6rem; }
            .block-container { padding-top: 1.5rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_login_gate() -> None:
    if not auth_enabled():
        return

    if is_authenticated():
        return

    _inject_login_styles()

    configured = _configured_users()
    if not configured:
        st.error(
            "Authentication is enabled but no user credentials are configured. "
            "Generate bcrypt password hashes and configure the RAI_* username/hash values."
        )
        st.stop()

    left, right = st.columns([1.45, 0.8], gap="large")

    with left:
        st.markdown(
            """
            <div class="rai-login-hero">
              <div>
                <div class="rai-login-kicker">Responsible AI Research Platform</div>
                <div class="rai-login-title">Digital Twin for governed AI validation.</div>
                <div class="rai-login-subtitle">
                  A controlled research environment for synthetic security simulation,
                  human oversight, policy-governed remediation, and auditable evidence.
                </div>
                <div class="rai-login-pills">
                  <span class="rai-login-pill">Synthetic data only</span>
                  <span class="rai-login-pill">Human oversight</span>
                  <span class="rai-login-pill">Auditable evidence</span>
                  <span class="rai-login-pill">Partner preview</span>
                </div>
              </div>
              <div class="rai-login-foot">
                Responsible AI Digital Twin · Controlled research prototype
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="rai-login-panel-title">Secure access</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="rai-login-panel-copy">Sign in with credentials issued by the project team. '
                'Partner accounts are read-only and intended for research review and feedback.</div>',
                unsafe_allow_html=True,
            )

            with st.form("rai-login", clear_on_submit=False):
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    autocomplete="username",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    autocomplete="current-password",
                )
                submitted = st.form_submit_button(
                    "Sign in",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if login(username, password):
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

            st.caption(
                "Authorized access only · Sessions expire automatically after the configured inactivity period."
            )

    st.stop()
