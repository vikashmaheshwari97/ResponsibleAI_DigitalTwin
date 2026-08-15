from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def get_setting(name: str, default: str | None = None) -> str | None:
    """Return a normal environment setting."""
    return os.getenv(name, default)


def get_secret(name: str, default: str | None = None) -> str | None:
    """
    Resolve a secret from either NAME_FILE or NAME.

    File-backed secrets are useful for Docker Compose/Swarm/Kubernetes style
    deployments while local development can continue to use a git-ignored
    .env file.
    """
    file_value = os.getenv(f"{name}_FILE")
    if file_value:
        path = Path(file_value)
        if not path.exists():
            raise RuntimeError(f"Secret file for {name} does not exist: {path}")
        return path.read_text(encoding="utf-8").strip()

    return os.getenv(name, default)


def get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)
