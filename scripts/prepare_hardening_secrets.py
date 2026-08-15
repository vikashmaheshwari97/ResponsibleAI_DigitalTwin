from __future__ import annotations

import argparse
from getpass import getpass
from pathlib import Path
import secrets
import sys

import bcrypt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SECRET_DIR = PROJECT_ROOT / "deploy" / "secrets"


def _write_secret(path: Path, value: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(
            f"Refusing to overwrite existing secret file: {path}. "
            "Use --force only when you intentionally want to rotate it."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.strip() + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


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


def _bcrypt_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create git-ignored file-backed secrets for the local production-style "
            "hardening smoke test. Secret values are never printed."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rotate and overwrite existing local hardening secret files.",
    )
    args = parser.parse_args()

    print("Responsible AI Digital Twin - Local Hardening Secret Preparation")
    print("These files stay under deploy/secrets/ and are ignored by Git.")
    print("No secret value will be printed.\n")

    admin_password = _prompt_password("Admin")
    operator_password = _prompt_password("Operator")
    auditor_password = _prompt_password("Auditor")

    values = {
        "postgres_password.txt": secrets.token_urlsafe(36),
        "sandbox_admin_token.txt": secrets.token_urlsafe(36),
        "admin_password_hash.txt": _bcrypt_hash(admin_password),
        "operator_password_hash.txt": _bcrypt_hash(operator_password),
        "auditor_password_hash.txt": _bcrypt_hash(auditor_password),
    }

    created = []
    try:
        for name, value in values.items():
            path = SECRET_DIR / name
            _write_secret(path, value, force=args.force)
            created.append(path)
    except Exception:
        # Do not leave a partially-created set on a first-time failure.
        if not args.force:
            for path in created:
                try:
                    path.unlink()
                except OSError:
                    pass
        raise

    print("\nPrepared local hardening secret files:")
    for path in created:
        print(f"  - {path.relative_to(PROJECT_ROOT)}")
    print("\nNext: generate local TLS material, then run:")
    print("  python scripts/validate_hardening_config.py")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
