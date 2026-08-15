from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str


class LoginResponse(BaseModel):
    username: str
    access_token: str


class SandboxConfigRequest(BaseModel):
    security_profile: Literal["vulnerable", "secure"] | None = None
    authorization_mode: Literal["vulnerable", "secure"] | None = None
    version: str = Field(min_length=1)
