from __future__ import annotations

import requests

from services.config_service import get_secret, get_setting


SANDBOX_BASE_URL = get_setting("SANDBOX_BASE_URL", "http://127.0.0.1:8001")


def _admin_token() -> str:
    value = get_secret("SANDBOX_ADMIN_TOKEN")
    if not value:
        raise RuntimeError(
            "SANDBOX_ADMIN_TOKEN is not configured. Copy .env.example to .env "
            "and set a local token, or provide SANDBOX_ADMIN_TOKEN_FILE."
        )
    return value


def get_sandbox_health() -> dict:
    try:
        response = requests.get(f"{SANDBOX_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "available": True,
            "status": data.get("status"),
            "application": data.get("application"),
            "version": data.get("version"),
            "security_profile": data.get(
                "security_profile", data.get("authorization_mode")
            ),
            "authorization_mode": data.get("authorization_mode"),
            "token_validation_mode": data.get("token_validation_mode"),
            "input_validation_mode": data.get("input_validation_mode"),
            "rate_limit_mode": data.get("rate_limit_mode"),
            "rate_limit_threshold": data.get("rate_limit_threshold"),
            "error": None,
        }
    except Exception as exc:
        return {
            "available": False,
            "status": "offline",
            "application": "SecureMessenger",
            "version": None,
            "security_profile": None,
            "authorization_mode": None,
            "token_validation_mode": None,
            "input_validation_mode": None,
            "rate_limit_mode": None,
            "rate_limit_threshold": None,
            "error": str(exc),
        }


def sandbox_is_available() -> bool:
    return bool(get_sandbox_health()["available"])


def configure_sandbox(profile: str, version: str) -> dict:
    if profile not in {"vulnerable", "secure"}:
        raise ValueError(f"Unsupported sandbox profile: {profile}")

    response = requests.post(
        f"{SANDBOX_BASE_URL}/admin/configure",
        headers={"X-Sandbox-Admin": _admin_token()},
        json={"security_profile": profile, "version": version},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def apply_secure_mode() -> dict:
    return configure_sandbox("secure", "1.1")


def reset_sandbox() -> dict:
    return configure_sandbox("vulnerable", "1.0")
