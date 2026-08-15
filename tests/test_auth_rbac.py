from __future__ import annotations

import pytest

bcrypt = pytest.importorskip("bcrypt")
pytest.importorskip("streamlit")

from services.auth_service import ROLE_ADMIN, ROLE_AUDITOR, ROLE_OPERATOR, verify_credentials


def test_configured_roles_can_be_verified(monkeypatch):
    cases = [
        ("RAI_ADMIN", "alice-admin", ROLE_ADMIN),
        ("RAI_OPERATOR", "olivia-operator", ROLE_OPERATOR),
        ("RAI_AUDITOR", "amy-auditor", ROLE_AUDITOR),
    ]

    password = "correct horse battery staple"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()

    for prefix, username, expected_role in cases:
        monkeypatch.setenv(f"{prefix}_USERNAME", username)
        monkeypatch.setenv(f"{prefix}_PASSWORD_HASH", password_hash)

    for _, username, expected_role in cases:
        identity = verify_credentials(username, password)
        assert identity is not None
        assert identity["role"] == expected_role

    assert verify_credentials("alice-admin", "wrong-password") is None
