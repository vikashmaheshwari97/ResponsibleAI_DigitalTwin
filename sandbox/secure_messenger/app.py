from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

from fastapi import Body, FastAPI, Header, HTTPException

try:
    from .database import (
        BOTS,
        EXPIRED_TOKENS,
        FEATURE_CONFIGS,
        GOVERNMENT_REQUESTS,
        INTEGRATIONS,
        MESSAGES,
        USERS,
    )
    from .models import (
        BotDataRequest,
        BulkExportRequest,
        FeatureRequest,
        GovernmentDataRequest,
        LoginRequest,
        LoginResponse,
        SandboxConfigRequest,
        ShareRequest,
    )
except ImportError:  # Docker runs this module as top-level ``app``.
    from database import (
        BOTS,
        EXPIRED_TOKENS,
        FEATURE_CONFIGS,
        GOVERNMENT_REQUESTS,
        INTEGRATIONS,
        MESSAGES,
        USERS,
    )
    from models import (
        BotDataRequest,
        BulkExportRequest,
        FeatureRequest,
        GovernmentDataRequest,
        LoginRequest,
        LoginResponse,
        SandboxConfigRequest,
        ShareRequest,
    )


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

BULK_EXPORT_THRESHOLD = 10
BULK_EXPORT_REQUESTS: dict[str, int] = defaultdict(int)

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


# ---------------------------------------------------------------------------
# Original endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    profile = _profile()
    return {
        "status": "healthy",
        "application": "SecureMessenger",
        "version": runtime_config["version"],
        "security_profile": profile,
        "authorization_mode": profile,
        "token_validation_mode": profile,
        "input_validation_mode": profile,
        "rate_limit_mode": profile,
        "rate_limit_threshold": RATE_LIMIT_THRESHOLD,
        "bulk_export_threshold": BULK_EXPORT_THRESHOLD,
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
    BULK_EXPORT_REQUESTS.clear()

    return {
        "status": "updated",
        "application": "SecureMessenger",
        "version": runtime_config["version"],
        "security_profile": profile,
        "authorization_mode": profile,
        "rate_counters_reset": True,
    }


# ---------------------------------------------------------------------------
# SCN-005: Bulk User-Data Exfiltration
# ---------------------------------------------------------------------------


@app.get("/export/messages")
def export_messages(
    limit: int = 1000000,
    authorization: str | None = Header(default=None),
):
    username = get_current_user(authorization)
    BULK_EXPORT_REQUESTS[username] += 1
    attempt = BULK_EXPORT_REQUESTS[username]

    if _is_secure() and attempt > BULK_EXPORT_THRESHOLD:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Bulk export rate threshold exceeded",
                "attempt": attempt,
                "threshold": BULK_EXPORT_THRESHOLD,
            },
        )

    if _is_secure() and limit > 100:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Export limit exceeds permitted bulk threshold",
                "requested_limit": limit,
                "maximum_allowed": 100,
            },
        )

    all_messages = list(MESSAGES.values())
    exported = all_messages[:limit]
    return {
        "exported_count": len(exported),
        "total_available": len(all_messages),
        "messages": exported,
    }


# ---------------------------------------------------------------------------
# SCN-006: Unauthorized Third-Party Data Sharing
# ---------------------------------------------------------------------------


@app.get("/integrations")
def list_integrations(authorization: str | None = Header(default=None)):
    get_current_user(authorization)

    if _is_secure():
        return [i for i in INTEGRATIONS.values() if i["authorized"]]

    return list(INTEGRATIONS.values())


@app.post("/share")
def share_data(
    request: ShareRequest,
    authorization: str | None = Header(default=None),
):
    username = get_current_user(authorization)
    integration = INTEGRATIONS.get(request.integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if _is_secure() and not integration["authorized"]:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Integration is not authorized for data sharing",
                "integration_id": request.integration_id,
                "integration_name": integration["display_name"],
                "authorized": False,
            },
        )

    return {
        "status": "shared",
        "integration_id": request.integration_id,
        "integration_name": integration["display_name"],
        "data_type": request.data_type,
        "shared_by": username,
        "authorized": integration["authorized"] if _is_secure() else True,
    }


# ---------------------------------------------------------------------------
# SCN-007: Government Data Request
# ---------------------------------------------------------------------------


@app.post("/legal/request")
def government_data_request(
    request: GovernmentDataRequest,
    authorization: str | None = Header(default=None),
):
    get_current_user(authorization)
    gov_request = GOVERNMENT_REQUESTS.get(request.request_id)

    if _is_secure():
        if not gov_request or not gov_request.get("legal_basis"):
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Government request lacks valid legal basis",
                    "request_id": request.request_id,
                    "entity": request.entity,
                    "legal_basis": request.legal_basis,
                    "authorized": False,
                },
            )
        if not gov_request.get("authorized"):
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Government request exceeds permitted data scope",
                    "request_id": request.request_id,
                    "entity": request.entity,
                    "requested_scope": request.scope,
                    "authorized": False,
                },
            )

    return {
        "status": "data_disclosed",
        "request_id": request.request_id,
        "entity": request.entity,
        "scope": request.scope,
        "legal_basis": request.legal_basis or "none_provided",
        "data_shared": list(MESSAGES.values()),
    }


# ---------------------------------------------------------------------------
# SCN-008: Malicious / Misbehaving Bot
# ---------------------------------------------------------------------------


@app.get("/bot/{bot_id}/data")
def bot_data_access(
    bot_id: str,
    data_type: str = "user_profiles",
    authorization: str | None = Header(default=None),
):
    get_current_user(authorization)
    bot = BOTS.get(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    required_permission = f"read_{data_type}"
    has_permission = required_permission in bot["permissions"]

    if _is_secure() and not has_permission:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Bot does not have the required permission",
                "bot_id": bot_id,
                "bot_name": bot["display_name"],
                "declared_purpose": bot["declared_purpose"],
                "required_permission": required_permission,
                "granted_permissions": bot["permissions"],
                "authorized": False,
            },
        )

    data: dict[str, Any] = {}
    if data_type == "user_profiles":
        data = {
            "users": [
                {"id": u["id"], "username": u["username"], "display_name": u["display_name"]}
                for u in USERS.values()
            ]
        }
    elif data_type == "message_history":
        data = {"messages": list(MESSAGES.values())}
    else:
        data = {"data_type": data_type, "note": "synthetic data returned"}

    return {
        "bot_id": bot_id,
        "bot_name": bot["display_name"],
        "declared_purpose": bot["declared_purpose"],
        "data_type": data_type,
        "data": data,
    }


# ---------------------------------------------------------------------------
# SCN-009: New Feature Safety Testing
# ---------------------------------------------------------------------------


@app.post("/feature/summarize")
def feature_summarize(
    request: FeatureRequest,
    authorization: str | None = Header(default=None),
):
    username = get_current_user(authorization)
    feature = FEATURE_CONFIGS.get(request.feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    requested_ids = request.message_ids or list(MESSAGES.keys())

    if _is_secure():
        scope = feature["declared_scope"]
        accessible = []
        for mid in requested_ids:
            msg = MESSAGES.get(mid)
            if not msg:
                continue
            if scope == "public_group_messages" and request.include_private:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": "Feature attempts to access private messages beyond declared scope",
                        "feature_id": request.feature_id,
                        "feature_name": feature["display_name"],
                        "declared_scope": scope,
                        "attempted_access": "private_messages",
                        "authorized": False,
                    },
                )
            if scope == "public_group_messages" and msg["owner"] != username:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": "Feature attempts to access other users private messages",
                        "feature_id": request.feature_id,
                        "feature_name": feature["display_name"],
                        "declared_scope": scope,
                        "message_id": mid,
                        "message_owner": msg["owner"],
                        "authorized": False,
                    },
                )
            accessible.append(msg)
    else:
        accessible = [MESSAGES[mid] for mid in requested_ids if mid in MESSAGES]

    summaries = [
        {"message_id": m["id"], "summary": f"Synthetic summary of: {m['content'][:50]}"}
        for m in accessible
    ]

    return {
        "feature_id": request.feature_id,
        "feature_name": feature["display_name"],
        "summarized_count": len(summaries),
        "summaries": summaries,
        "sends_to_external_model": feature["sends_to_external_model"],
    }
