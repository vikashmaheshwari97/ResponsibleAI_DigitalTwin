from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import streamlit as st

from services.config_service import get_bool, get_int, get_secret, get_setting


ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_AUDITOR = "auditor"
ALL_ROLES = {ROLE_ADMIN, ROLE_OPERATOR, ROLE_AUDITOR}


def auth_enabled() -> bool:
    return get_bool("AUTH_ENABLED", False)


def _configured_users() -> list[dict]:
    users: list[dict] = []
    for role, prefix in [
        (ROLE_ADMIN, "RAI_ADMIN"),
        (ROLE_OPERATOR, "RAI_OPERATOR"),
        (ROLE_AUDITOR, "RAI_AUDITOR"),
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


def can_execute_scenarios() -> bool:
    return current_role() in {ROLE_ADMIN, ROLE_OPERATOR}


def can_manage_governance() -> bool:
    return current_role() == ROLE_ADMIN


def can_view_governance() -> bool:
    return current_role() in ALL_ROLES


def can_view_reports() -> bool:
    return current_role() in ALL_ROLES


def can_view_analytics() -> bool:
    return current_role() in ALL_ROLES


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


def render_login_gate() -> None:
    if not auth_enabled():
        return

    if is_authenticated():
        return

    st.title("🔐 Responsible AI Digital Twin")
    st.caption("Authentication is enabled for this environment.")

    configured = _configured_users()
    if not configured:
        st.error(
            "AUTH_ENABLED=true but no password hashes are configured. "
            "Use scripts/generate_password_hash.py and configure one or more "
            "RAI_*_PASSWORD_HASH values."
        )
        st.stop()

    with st.form("rai-login", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if login(username, password):
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info(
        "Roles: admin = full access, operator = execute validation workflows, "
        "auditor = read-only evidence/governance access."
    )
    st.stop()
