from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException

from database import MESSAGES, USERS
from models import LoginRequest, LoginResponse, SandboxConfigRequest


DEFAULT_VERSION = os.getenv(
    "APP_VERSION",
    "1.0",
)

DEFAULT_AUTHORIZATION_MODE = os.getenv(
    "AUTHORIZATION_MODE",
    "vulnerable",
)

SANDBOX_ADMIN_TOKEN = os.getenv(
    "SANDBOX_ADMIN_TOKEN"
)

if not SANDBOX_ADMIN_TOKEN:
    raise RuntimeError(
        "SANDBOX_ADMIN_TOKEN must be supplied to the sandbox container."
    )


runtime_config = {
    "version": DEFAULT_VERSION,
    "authorization_mode": DEFAULT_AUTHORIZATION_MODE,
}


app = FastAPI(
    title="SecureMessenger Digital Twin",
    version=DEFAULT_VERSION,
    description=(
        "Synthetic messaging application used only inside the "
        "Responsible AI Digital Twin PoC sandbox."
    ),
)


def get_current_user(
    authorization: str | None,
) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
        )

    token = (
        authorization
        .removeprefix("Bearer ")
        .strip()
    )

    for username, user in USERS.items():
        if user["token"] == token:
            return username

    raise HTTPException(
        status_code=401,
        detail="Invalid access token",
    )


def require_admin(
    x_sandbox_admin: str | None,
) -> None:
    if (
        x_sandbox_admin
        != SANDBOX_ADMIN_TOKEN
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Invalid sandbox admin token"
            ),
        )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "SecureMessenger",
        "version": runtime_config[
            "version"
        ],
        "authorization_mode": (
            runtime_config[
                "authorization_mode"
            ]
        ),
    }


@app.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    request: LoginRequest,
):
    user = USERS.get(
        request.username.lower()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail=(
                "Synthetic user not found"
            ),
        )

    return {
        "username": user[
            "username"
        ],
        "access_token": user[
            "token"
        ],
    }


@app.get("/users/me")
def current_user(
    authorization: str | None = Header(
        default=None
    ),
):
    username = get_current_user(
        authorization
    )

    user = USERS[username]

    return {
        "id": user["id"],
        "username": user[
            "username"
        ],
        "display_name": user[
            "display_name"
        ],
    }


@app.get("/messages")
def list_messages(
    authorization: str | None = Header(
        default=None
    ),
):
    username = get_current_user(
        authorization
    )

    return [
        message
        for message in MESSAGES.values()
        if message["owner"] == username
    ]


@app.get("/messages/{message_id}")
def get_message(
    message_id: str,
    authorization: str | None = Header(
        default=None
    ),
):
    username = get_current_user(
        authorization
    )

    message = MESSAGES.get(
        message_id
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    # Intentionally vulnerable PoC mode:
    # authentication succeeds but ownership is not enforced.
    #
    # Controlled secure mode:
    # the exact same endpoint requires message ownership.
    if (
        runtime_config[
            "authorization_mode"
        ]
        == "secure"
        and message["owner"]
        != username
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Authenticated user "
                "does not own this message."
            ),
        )

    return message


@app.post("/admin/configure")
def configure_sandbox(
    request: SandboxConfigRequest,
    x_sandbox_admin: str | None = Header(
        default=None
    ),
):
    require_admin(
        x_sandbox_admin
    )

    runtime_config[
        "authorization_mode"
    ] = request.authorization_mode

    runtime_config[
        "version"
    ] = request.version

    return {
        "status": "updated",
        "application": "SecureMessenger",
        "version": runtime_config[
            "version"
        ],
        "authorization_mode": (
            runtime_config[
                "authorization_mode"
            ]
        ),
    }
