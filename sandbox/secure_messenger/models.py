from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str


class LoginResponse(BaseModel):
    username: str
    access_token: str


class SandboxConfigRequest(BaseModel):
    authorization_mode: str = Field(pattern="^(vulnerable|secure)$")
    version: str
