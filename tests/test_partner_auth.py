from __future__ import annotations

import bcrypt

import services.auth_service as auth


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def test_partner_credentials_are_discovered_and_verified(monkeypatch):
    password = "partner-password-123"
    monkeypatch.setenv("RAI_PARTNER_USERNAME", "research-partner")
    monkeypatch.setenv("RAI_PARTNER_PASSWORD_HASH", _hash(password))

    identity = auth.verify_credentials("research-partner", password)

    assert identity is not None
    assert identity["username"] == "research-partner"
    assert identity["role"] == auth.ROLE_PARTNER
    assert identity["authenticated"] is True


def test_partner_wrong_password_is_rejected(monkeypatch):
    monkeypatch.setenv("RAI_PARTNER_USERNAME", "research-partner")
    monkeypatch.setenv("RAI_PARTNER_PASSWORD_HASH", _hash("correct-password-123"))

    assert auth.verify_credentials("research-partner", "wrong-password") is None


def test_partner_is_read_only(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setattr(
        auth.st,
        "session_state",
        {
            "auth_identity": {
                "username": "research-partner",
                "role": auth.ROLE_PARTNER,
                "authenticated": True,
                "auth_mode": "password",
            }
        },
    )

    assert auth.can_execute_scenarios() is False
    assert auth.can_manage_governance() is False
    assert auth.can_view_internal_governance() is False
    assert auth.can_view_reports() is True
    assert auth.can_view_analytics() is True
    assert auth.can_view_governance() is True


def test_operator_execution_permissions_remain_unchanged(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setattr(
        auth.st,
        "session_state",
        {
            "auth_identity": {
                "username": "operator",
                "role": auth.ROLE_OPERATOR,
                "authenticated": True,
                "auth_mode": "password",
            }
        },
    )

    assert auth.can_execute_scenarios() is True
    assert auth.can_manage_governance() is False
