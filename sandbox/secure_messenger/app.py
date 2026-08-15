from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

from fastapi import Body, FastAPI, Header, HTTPException

try:
    from .database import EXPIRED_TOKENS, MESSAGES, USERS
    from .models import LoginRequest, LoginResponse, SandboxConfigRequest
except ImportError:  # Docker runs this module as top-level ``app``.
    from database import EXPIRED_TOKENS, MESSAGES, USERS
    from models import LoginRequest, LoginResponse, SandboxConfigRequest


DEFAULT_VERSION = os.getenv("APP_VERSION", "1.0")
DEFAULT_PROFILE = os.getenv(
    "SECURITY_PROFILE",
    os.getenv("AUTHORIZATION_MODE", "vulnerable"),
)


def _read_secret(name: str) -> str | None:
    file_name = os.getenv(f"{name}_FILE")
    if file_name:
        with open(file_name, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    return os.getenv(name)


SANDBOX_ADMIN_TOKEN = _read_secret("SANDBOX_ADMIN_TOKEN")
if not SANDBOX_ADMIN_TOKEN:
    raise RuntimeError("SANDBOX_ADMIN_TOKEN must be supplied to the sandbox container.")

RATE_LIMIT_THRESHOLD = 5
RATE_TEST_REQUESTS: dict[str, int] = defaultdict(int)

runtime_config = {
    "version": DEFAULT_VERSION,
    "security_profile": DEFAULT_PROFILE,
}

app = FastAPI(
    title="SecureMessenger Digital Twin",
    version=DEFAULT_VERSION,
    description=(
        "Synthetic messaging application used only inside the Responsible AI "
        "Digital Twin controlled sandbox."
    ),
)


def _profile() -> str:
    return runtime_config["security_profile"]


def _is_secure() -> bool:
    return _profile() == "secure"


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Access token missing")
    return token


def get_current_user(authorization: str | None) -> str:
    token = _bearer_token(authorization)

    for username, user in USERS.items():
        if user["token"] == token:
            return username

    expired_owner = EXPIRED_TOKENS.get(token)
    if expired_owner:
        if _is_secure():
            raise HTTPException(status_code=401, detail="Synthetic token expired")
        return expired_owner

    raise HTTPException(status_code=401, detail="Invalid access token")


def require_admin(x_sandbox_admin: str | None) -> None:
    if x_sandbox_admin != SANDBOX_ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid sandbox admin token")


def _validate_message_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed_keys = {"recipient", "body", "priority"}
    unexpected = sorted(set(payload) - allowed_keys)
    if unexpected:
        errors.append(f"Unexpected field(s): {', '.join(unexpected)}")

    recipient = payload.get("recipient")
    body = payload.get("body")
    priority = payload.get("priority")

    if recipient not in USERS:
        errors.append("recipient must reference a synthetic user")
    if not isinstance(body, str) or not body.strip():
        errors.append("body must be a non-empty string")
    elif len(body) > 500:
        errors.append("body exceeds 500 characters")
    if not isinstance(priority, int) or isinstance(priority, bool) or not 1 <= priority <= 5:
        errors.append("priority must be an integer between 1 and 5")

    return errors


@app.get("/health")
def health():
    profile = _profile()
    return {
        "status": "healthy",
        "application": "SecureMessenger",
        "version": runtime_config["version"],
        "security_profile": profile,
        # Compatibility for the original UI and older evidence bundles.
        "authorization_mode": profile,
        "token_validation_mode": profile,
        "input_validation_mode": profile,
        "rate_limit_mode": profile,
        "rate_limit_threshold": RATE_LIMIT_THRESHOLD,
    }


@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = USERS.get(request.username.lower())
    if not user:
        raise HTTPException(status_code=404, detail="Synthetic user not found")
    return {"username": user["username"], "access_token": user["token"]}


@app.get("/users/me")
def current_user(authorization: str | None = Header(default=None)):
    username = get_current_user(authorization)
    user = USERS[username]
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
    }


@app.get("/messages")
def list_messages(authorization: str | None = Header(default=None)):
    username = get_current_user(authorization)
    return [message for message in MESSAGES.values() if message["owner"] == username]


@app.get("/messages/{message_id}")
def get_message(
    message_id: str,
    authorization: str | None = Header(default=None),
):
    username = get_current_user(authorization)
    message = MESSAGES.get(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if _is_secure() and message["owner"] != username:
        raise HTTPException(
            status_code=403,
            detail="Authenticated user does not own this message.",
        )

    return message


@app.post("/messages", status_code=201)
def create_message(
    payload: dict[str, Any] = Body(...),
    authorization: str | None = Header(default=None),
):
    username = get_current_user(authorization)
    errors = _validate_message_payload(payload)

    if _is_secure() and errors:
        raise HTTPException(status_code=422, detail=errors)

    # Synthetic response only; no malformed message is persisted.
    return {
        "id": "MSG-SYNTHETIC-PREVIEW",
        "owner": username,
        "accepted": True,
        "validation_errors_ignored": errors if not _is_secure() else [],
        "payload": payload,
    }


@app.post("/rate-test")
def rate_test(authorization: str | None = Header(default=None)):
    username = get_current_user(authorization)
    RATE_TEST_REQUESTS[username] += 1
    attempt = RATE_TEST_REQUESTS[username]

    if _is_secure() and attempt > RATE_LIMIT_THRESHOLD:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Synthetic local rate threshold exceeded",
                "attempt": attempt,
                "threshold": RATE_LIMIT_THRESHOLD,
            },
        )

    return {
        "status": "accepted",
        "username": username,
        "attempt": attempt,
        "threshold": RATE_LIMIT_THRESHOLD,
    }


@app.post("/admin/configure")
def configure_sandbox(
    request: SandboxConfigRequest,
    x_sandbox_admin: str | None = Header(default=None),
):
    require_admin(x_sandbox_admin)

    profile = request.security_profile or request.authorization_mode
    if not profile:
        raise HTTPException(status_code=422, detail="security_profile is required")

    runtime_config["security_profile"] = profile
    runtime_config["version"] = request.version
    RATE_TEST_REQUESTS.clear()

    return {
        "status": "updated",
        "application": "SecureMessenger",
        "version": runtime_config["version"],
        "security_profile": profile,
        "authorization_mode": profile,
        "rate_counters_reset": True,
    }
