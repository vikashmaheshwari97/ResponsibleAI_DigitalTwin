from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.config_service import get_setting  # noqa: E402


def _default_latest_backup() -> Path | None:
    backup_dir = Path(get_setting("BACKUP_DIR", "backups") or "backups")
    if not backup_dir.is_absolute():
        backup_dir = PROJECT_ROOT / backup_dir
    backups = sorted(
        backup_dir.glob("*.sql.gz") if backup_dir.exists() else [],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return backups[0] if backups else None


def verify_backup(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)

    digest = hashlib.sha256()
    decompressed_bytes = 0
    preview = b""
    with path.open("rb") as raw:
        for chunk in iter(lambda: raw.read(1024 * 1024), b""):
            digest.update(chunk)

    with gzip.open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            if len(preview) < 8192:
                preview += chunk[: 8192 - len(preview)]
            decompressed_bytes += len(chunk)

    looks_like_dump = (
        b"PostgreSQL database dump" in preview
        or b"SET statement_timeout" in preview
        or b"CREATE TABLE" in preview
    )
    age_hours = (
        datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
    ) / 3600.0

    return {
        "path": str(path.resolve()),
        "compressed_bytes": path.stat().st_size,
        "decompressed_bytes": decompressed_bytes,
        "sha256": digest.hexdigest(),
        "age_hours": max(0.0, age_hours),
        "gzip_valid": True,
        "looks_like_postgresql_dump": looks_like_dump,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify gzip integrity and basic PostgreSQL-dump characteristics of an evidence backup."
    )
    parser.add_argument("backup", nargs="?", type=Path)
    args = parser.parse_args()

    path = args.backup or _default_latest_backup()
    if path is None:
        print("No .sql.gz backup found. Run: python scripts/backup_database.py")
        raise SystemExit(1)

    try:
        result = verify_backup(path)
    except (OSError, EOFError) as exc:
        print(f"BACKUP VERIFICATION: FAIL\n{exc}")
        raise SystemExit(1)

    print("Responsible AI Digital Twin - Backup Verification")
    print("=" * 67)
    print(f"File:                {result['path']}")
    print(f"Compressed bytes:    {result['compressed_bytes']}")
    print(f"Decompressed bytes:  {result['decompressed_bytes']}")
    print(f"Age:                 {result['age_hours']:.1f} hours")
    print(f"SHA-256:             {result['sha256']}")
    print(f"PostgreSQL signature:{' PASS' if result['looks_like_postgresql_dump'] else ' WARN'}")

    if result["decompressed_bytes"] <= 0:
        print("BACKUP VERIFICATION: FAIL")
        raise SystemExit(1)

    print("BACKUP VERIFICATION: PASS")


if __name__ == "__main__":
    main()
