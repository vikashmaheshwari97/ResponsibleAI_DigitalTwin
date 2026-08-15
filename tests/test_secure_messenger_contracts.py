from __future__ import annotations

import os

os.environ.setdefault("SANDBOX_ADMIN_TOKEN", "ci_dummy")

from fastapi.testclient import TestClient

from sandbox.secure_messenger.app import app


client = TestClient(app)
ADMIN_HEADERS = {"X-Sandbox-Admin": os.environ["SANDBOX_ADMIN_TOKEN"]}


def _configure(profile: str, version: str) -> None:
    response = client.post(
        "/admin/configure",
        headers=ADMIN_HEADERS,
        json={"security_profile": profile, "version": version},
    )
    assert response.status_code == 200


def _login(username: str = "alice") -> str:
    response = client.post("/login", json={"username": username})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_scn001_bola_contract():
    token = _login("alice")

    _configure("vulnerable", "1.0")
    vulnerable = client.get("/messages/MSG-204", headers=_auth(token))
    assert vulnerable.status_code == 200
    assert vulnerable.json()["owner"] == "bob"

    _configure("secure", "1.1")
    secure = client.get("/messages/MSG-204", headers=_auth(token))
    assert secure.status_code == 403


def test_scn002_expired_token_contract():
    expired = _auth("expired-token-alice")

    _configure("vulnerable", "1.0")
    assert client.get("/users/me", headers=expired).status_code == 200

    _configure("secure", "1.1")
    assert client.get("/users/me", headers=expired).status_code == 401


def test_scn003_input_validation_contract():
    token = _login("alice")
    payload = {
        "recipient": "bob",
        "body": "",
        "priority": 99,
        "unexpected": "synthetic-field",
    }

    _configure("vulnerable", "1.0")
    assert client.post("/messages", headers=_auth(token), json=payload).status_code == 201

    _configure("secure", "1.1")
    assert client.post("/messages", headers=_auth(token), json=payload).status_code == 422


def test_scn004_rate_control_contract():
    token = _login("alice")

    _configure("vulnerable", "1.0")
    statuses = [
        client.post("/rate-test", headers=_auth(token)).status_code
        for _ in range(8)
    ]
    assert statuses[-1] == 200

    _configure("secure", "1.1")
    statuses = [
        client.post("/rate-test", headers=_auth(token)).status_code
        for _ in range(8)
    ]
    assert statuses[-1] == 429
