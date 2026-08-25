from __future__ import annotations

import argparse
from datetime import datetime
from getpass import getpass
from pathlib import Path
import shutil
import sys

import bcrypt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

ROLE_DEFAULTS = {
    "admin": ("RAI_ADMIN", "admin"),
    "operator": ("RAI_OPERATOR", "operator"),
    "auditor": ("RAI_AUDITOR", "auditor"),
    "partner": ("RAI_PARTNER", "partner"),
}


def _bcrypt_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _prompt_password(label: str) -> str:
    first = getpass(f"{label} password: ")
    second = getpass(f"Confirm {label} password: ")
    if not first:
        raise ValueError(f"{label} password cannot be empty.")
    if first != second:
        raise ValueError(f"{label} passwords do not match.")
    if len(first) < 12:
        raise ValueError(f"{label} password must contain at least 12 characters.")
    return first


def _read_env_lines(path: Path) -> list[str]:
    if path.exists():
        return path.read_text(encoding="utf-8").splitlines()
    if ENV_EXAMPLE.exists():
        return ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
    return []


def _upsert(lines: list[str], key: str, value: str) -> list[str]:
    prefix = f"{key}="
    output: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(prefix):
            if not replaced:
                output.append(f"{key}={value}")
                replaced = True
            continue
        output.append(line)
    if not replaced:
        if output and output[-1].strip():
            output.append("")
        output.append(f"{key}={value}")
    return output


def configure_role(lines: list[str], role: str, username: str, password: str) -> list[str]:
    prefix, _ = ROLE_DEFAULTS[role]
    password_hash = _bcrypt_hash(password)
    # Defensive self-check before writing anything.
    if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
        raise RuntimeError(f"Generated bcrypt hash failed verification for {role}.")
    lines = _upsert(lines, f"{prefix}_USERNAME", username)
    lines = _upsert(lines, f"{prefix}_PASSWORD_HASH", password_hash)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Configure local bcrypt credentials for Responsible AI Digital Twin roles. "
            "Plaintext passwords are never written to disk or printed."
        )
    )
    parser.add_argument(
        "--roles",
        nargs="+",
        choices=list(ROLE_DEFAULTS),
        default=list(ROLE_DEFAULTS),
        help="Roles to configure. Default: all four roles.",
    )
    args = parser.parse_args()

    print("Responsible AI Digital Twin - Role Credential Setup")
    print("Passwords are bcrypt-hashed and only hashes are written to .env.")
    print("Existing PostgreSQL, sandbox, and Ollama settings are preserved.\n")

    lines = _read_env_lines(ENV_PATH)
    lines = _upsert(lines, "AUTH_ENABLED", "true")
    # Keep an existing timeout if present; otherwise establish the default.
    if not any(line.startswith("AUTH_SESSION_TIMEOUT_MINUTES=") for line in lines):
        lines = _upsert(lines, "AUTH_SESSION_TIMEOUT_MINUTES", "60")

    configured: list[tuple[str, str]] = []
    for role in args.roles:
        prefix, default_username = ROLE_DEFAULTS[role]
        current = next(
            (line.split("=", 1)[1] for line in lines if line.startswith(f"{prefix}_USERNAME=")),
            default_username,
        ) or default_username
        entered = input(f"{role.title()} username [{current}]: ").strip()
        username = entered or current
        password = _prompt_password(role.title())
        lines = configure_role(lines, role, username, password)
        configured.append((role, username))

    if ENV_PATH.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = PROJECT_ROOT.parent / f"{PROJECT_ROOT.name}_auth_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"env-{stamp}.backup"
        shutil.copy2(ENV_PATH, backup)
        print(f"\nBackup created outside Git repo: {backup}")

    ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print("\nConfigured roles:")
    for role, username in configured:
        print(f"  - {role:<8} username={username}")
    print("\nNo plaintext password was stored or printed.")
    print("Restart Streamlit before testing the new credentials.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
