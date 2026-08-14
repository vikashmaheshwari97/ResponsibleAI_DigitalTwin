from __future__ import annotations

import requests

SANDBOX_BASE_URL = "http://127.0.0.1:8001"


def login(username: str) -> dict:
    response = requests.post(
        f"{SANDBOX_BASE_URL}/login",
        json={"username": username},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def request_message(token: str, message_id: str) -> dict:
    response = requests.get(
        f"{SANDBOX_BASE_URL}/messages/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}
    return {"status_code": response.status_code, "body": body}


def run_cross_user_message_test() -> dict:
    login_result = login("alice")
    response = request_message(login_result["access_token"], "MSG-204")
    observed_status = response["status_code"]
    body = response["body"]
    observed_owner = body.get("owner")
    unauthorized_access = observed_status == 200 and observed_owner == "bob"
    passed = observed_status == 403 and not unauthorized_access

    return {
        "scenario": "Unauthorized Private Message Access",
        "requesting_user": "alice",
        "resource_id": "MSG-204",
        "expected_owner": "bob",
        "observed_owner": observed_owner,
        "expected_status": 403,
        "observed_status": observed_status,
        "access_granted": observed_status == 200,
        "vulnerability_detected": unauthorized_access,
        "response": body,
        "result": "PASS" if passed else "FAIL",
    }


def format_security_evidence(result: dict) -> str:
    return f"""
Controlled Digital Twin security validation result

Scenario: {result['scenario']}
Sandbox application: SecureMessenger
Authenticated user: {result['requesting_user']}
Requested resource: {result['resource_id']}
Expected resource owner: {result['expected_owner']}
Observed resource owner: {result['observed_owner']}
Expected HTTP response: {result['expected_status']}
Observed HTTP response: {result['observed_status']}
Access granted: {result['access_granted']}
Vulnerability detected: {result['vulnerability_detected']}
Validation result: {result['result']}

This test was executed only against the locally isolated synthetic SecureMessenger Digital Twin.
""".strip()
