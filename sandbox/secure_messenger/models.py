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


class BulkExportRequest(BaseModel):
    format: str = "json"
    limit: int = Field(default=1000000, ge=1)


class ShareRequest(BaseModel):
    integration_id: str
    data_type: str = "user_messages"
    recipient_token: str = ""


class GovernmentDataRequest(BaseModel):
    request_id: str
    entity: str
    request_type: str = "user_data_access"
    scope: str = "all_user_messages"
    legal_basis: str | None = None


class BotDataRequest(BaseModel):
    bot_id: str
    data_type: str = "user_profiles"


class FeatureRequest(BaseModel):
    feature_id: str
    message_ids: list[str] = Field(default_factory=list)
    include_private: bool = False
