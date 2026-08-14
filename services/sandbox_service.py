from __future__ import annotations

import os

import requests
from dotenv import load_dotenv


load_dotenv()


SANDBOX_BASE_URL = os.getenv(
    "SANDBOX_BASE_URL",
    "http://127.0.0.1:8001",
)

SANDBOX_ADMIN_TOKEN = os.getenv(
    "SANDBOX_ADMIN_TOKEN"
)


def _require_admin_token() -> str:
    if not SANDBOX_ADMIN_TOKEN:
        raise RuntimeError(
            "SANDBOX_ADMIN_TOKEN is not configured. "
            "Copy .env.example to .env and set a local token."
        )

    return SANDBOX_ADMIN_TOKEN


def get_sandbox_health() -> dict:
    try:
        response = requests.get(
            f"{SANDBOX_BASE_URL}/health",
            timeout=5,
        )

        response.raise_for_status()
        data = response.json()

        return {
            "available": True,
            "status": data.get("status"),
            "application": data.get("application"),
            "version": data.get("version"),
            "authorization_mode": data.get(
                "authorization_mode"
            ),
            "error": None,
        }

    except Exception as exc:
        return {
            "available": False,
            "status": "offline",
            "application": "SecureMessenger",
            "version": None,
            "authorization_mode": None,
            "error": str(exc),
        }


def sandbox_is_available() -> bool:
    return bool(
        get_sandbox_health()[
            "available"
        ]
    )


def _configure_sandbox(
    mode: str,
    version: str,
) -> dict:
    response = requests.post(
        f"{SANDBOX_BASE_URL}/admin/configure",
        headers={
            "X-Sandbox-Admin": (
                _require_admin_token()
            )
        },
        json={
            "authorization_mode": mode,
            "version": version,
        },
        timeout=5,
    )

    response.raise_for_status()
    return response.json()


def apply_secure_mode() -> dict:
    return _configure_sandbox(
        mode="secure",
        version="1.1",
    )


def reset_sandbox() -> dict:
    return _configure_sandbox(
        mode="vulnerable",
        version="1.0",
    )
