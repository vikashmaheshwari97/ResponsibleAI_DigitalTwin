from __future__ import annotations

from typing import Any

import requests

from services.config_service import get_setting
from services.scenario_registry_service import get_scenario


SANDBOX_BASE_URL = get_setting("SANDBOX_BASE_URL", "http://127.0.0.1:8001")
REQUEST_TIMEOUT = 5


def _safe_body(response: requests.Response) -> dict | list | str:
    try:
        return response.json()
    except Exception:
        return {"raw": response.text}


def login(username: str) -> dict:
    response = requests.post(
        f"{SANDBOX_BASE_URL}/login",
        json={"username": username},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _authorized_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _standard_result(
    *,
    scenario_id: str,
    requesting_user: str,
    resource_id: str,
    expected_status: int,
    observed_status: int,
    response: Any,
    expected_owner: str | None = None,
    observed_owner: str | None = None,
    access_granted: bool = False,
    vulnerability_detected: bool,
    request_summary: str,
) -> dict:
    scenario = get_scenario(scenario_id)
    passed = observed_status == expected_status and not vulnerability_detected
    return {
        "scenario_id": scenario.scenario_id,
        "scenario": scenario.name,
        "category": scenario.category,
        "requesting_user": requesting_user,
        "resource_id": resource_id,
        "expected_owner": expected_owner,
        "observed_owner": observed_owner,
        "expected_status": expected_status,
        "observed_status": observed_status,
        "access_granted": access_granted,
        "vulnerability_detected": vulnerability_detected,
        "response": response,
        "request_summary": request_summary,
        "result": "PASS" if passed else "FAIL",
    }


def _run_bola() -> dict:
    scenario = get_scenario("SCN-001")
    login_result = login("alice")
    response = requests.get(
        f"{SANDBOX_BASE_URL}/messages/MSG-204",
        headers=_authorized_headers(login_result["access_token"]),
        timeout=REQUEST_TIMEOUT,
    )
    body = _safe_body(response)
    observed_owner = body.get("owner") if isinstance(body, dict) else None
    unauthorized_access = response.status_code == 200 and observed_owner == "bob"
    return _standard_result(
        scenario_id=scenario.scenario_id,
        requesting_user="alice",
        resource_id="MSG-204",
        expected_owner="bob",
        observed_owner=observed_owner,
        expected_status=scenario.expected_status,
        observed_status=response.status_code,
        access_granted=response.status_code == 200,
        vulnerability_detected=unauthorized_access,
        response=body,
        request_summary="Alice requests Bob's synthetic MSG-204.",
    )


def _run_expired_token() -> dict:
    scenario = get_scenario("SCN-002")
    token = "expired-token-alice"
    response = requests.get(
        f"{SANDBOX_BASE_URL}/users/me",
        headers=_authorized_headers(token),
        timeout=REQUEST_TIMEOUT,
    )
    body = _safe_body(response)
    vulnerability = response.status_code != scenario.expected_status
    return _standard_result(
        scenario_id=scenario.scenario_id,
        requesting_user="alice-expired-token",
        resource_id="/users/me",
        expected_status=scenario.expected_status,
        observed_status=response.status_code,
        access_granted=200 <= response.status_code < 300,
        vulnerability_detected=vulnerability,
        response=body,
        request_summary="Use the predefined expired synthetic Alice token at /users/me.",
    )


def _run_malformed_payload() -> dict:
    scenario = get_scenario("SCN-003")
    login_result = login("alice")
    malformed_payload = {
        "recipient": "bob",
        "body": "",
        "priority": 99,
        "unexpected": "synthetic-field",
    }
    response = requests.post(
        f"{SANDBOX_BASE_URL}/messages",
        headers=_authorized_headers(login_result["access_token"]),
        json=malformed_payload,
        timeout=REQUEST_TIMEOUT,
    )
    body = _safe_body(response)
    vulnerability = response.status_code != scenario.expected_status
    return _standard_result(
        scenario_id=scenario.scenario_id,
        requesting_user="alice",
        resource_id="POST /messages",
        expected_status=scenario.expected_status,
        observed_status=response.status_code,
        access_granted=200 <= response.status_code < 300,
        vulnerability_detected=vulnerability,
        response={"request": malformed_payload, "response": body},
        request_summary=(
            "Submit an empty body, priority=99 and an unexpected field to POST /messages."
        ),
    )


def _run_rate_limit() -> dict:
    scenario = get_scenario("SCN-004")
    login_result = login("alice")
    token = login_result["access_token"]
    attempts: list[dict] = []
    last_status = 0

    for attempt in range(1, 9):
        response = requests.post(
            f"{SANDBOX_BASE_URL}/rate-test",
            headers=_authorized_headers(token),
            timeout=REQUEST_TIMEOUT,
        )
        body = _safe_body(response)
        last_status = response.status_code
        attempts.append(
            {
                "attempt": attempt,
                "status_code": response.status_code,
                "body": body,
            }
        )

    vulnerability = last_status != scenario.expected_status
    return _standard_result(
        scenario_id=scenario.scenario_id,
        requesting_user="alice",
        resource_id="POST /rate-test × 8",
        expected_status=scenario.expected_status,
        observed_status=last_status,
        access_granted=last_status != 429,
        vulnerability_detected=vulnerability,
        response={"attempts": attempts, "final_status": last_status},
        request_summary="Send exactly eight localhost requests to the dedicated rate-test endpoint.",
    )


_RUNNERS = {
    "bola": _run_bola,
    "expired_token": _run_expired_token,
    "malformed_payload": _run_malformed_payload,
    "rate_limit": _run_rate_limit,
}


def run_scenario_test(scenario_id: str) -> dict:
    scenario = get_scenario(scenario_id)
    runner = _RUNNERS[scenario.test_kind]
    return runner()


def format_security_evidence(result: dict) -> str:
    return (
        "Controlled Digital Twin security validation result\n\n"
        f"Scenario ID: {result.get('scenario_id')}\n"
        f"Scenario: {result['scenario']}\n"
        f"Category: {result.get('category')}\n"
        "Sandbox application: SecureMessenger\n"
        f"Requesting synthetic identity: {result['requesting_user']}\n"
        f"Resource / endpoint: {result['resource_id']}\n"
        f"Request summary: {result.get('request_summary')}\n"
        f"Expected HTTP response: {result['expected_status']}\n"
        f"Observed HTTP response: {result['observed_status']}\n"
        f"Access granted: {result['access_granted']}\n"
        f"Vulnerability detected: {result['vulnerability_detected']}\n"
        f"Validation result: {result['result']}\n\n"
        "This test was executed only against the locally isolated synthetic "
        "SecureMessenger Digital Twin."
    )
