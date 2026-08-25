from __future__ import annotations

import bcrypt

import services.auth_service as auth


def _identity(role: str) -> dict:
    return {
        "auth_identity": {
            "username": role,
            "role": role,
            "authenticated": True,
            "auth_mode": "password",
        }
    }


def test_role_access_matrix_is_complete():
    assert set(auth.ROLE_ACCESS) == {
        auth.ROLE_ADMIN,
        auth.ROLE_OPERATOR,
        auth.ROLE_AUDITOR,
        auth.ROLE_PARTNER,
    }


def test_admin_has_full_access():
    p = auth.access_profile(auth.ROLE_ADMIN)
    assert all(p.values())


def test_operator_can_execute_but_cannot_access_internal_governance():
    p = auth.access_profile(auth.ROLE_OPERATOR)
    assert p["execute"] is True
    assert p["run_history"] is True
    assert p["readiness"] is True
    assert p["compliance"] is False
    assert p["audit"] is False
    assert p["manage_governance"] is False


def test_auditor_is_read_only_with_internal_governance_access():
    p = auth.access_profile(auth.ROLE_AUDITOR)
    assert p["execute"] is False
    assert p["readiness"] is True
    assert p["compliance"] is True
    assert p["audit"] is True
    assert p["manage_governance"] is False


def test_partner_is_curated_read_only():
    p = auth.access_profile(auth.ROLE_PARTNER)
    assert p["execute"] is False
    assert p["run_history"] is True
    assert p["analytics"] is True
    assert p["reports"] is True
    assert p["compliance"] is True
    assert p["readiness"] is False
    assert p["audit"] is False


def test_all_four_credentials_can_be_discovered(monkeypatch):
    role_prefix = {
        auth.ROLE_ADMIN: "RAI_ADMIN",
        auth.ROLE_OPERATOR: "RAI_OPERATOR",
        auth.ROLE_AUDITOR: "RAI_AUDITOR",
        auth.ROLE_PARTNER: "RAI_PARTNER",
    }
    for role, prefix in role_prefix.items():
        password = f"{role}-password-2026!"
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        monkeypatch.setenv(f"{prefix}_USERNAME", role)
        monkeypatch.setenv(f"{prefix}_PASSWORD_HASH", password_hash)
        identity = auth.verify_credentials(role, password)
        assert identity is not None
        assert identity["role"] == role
