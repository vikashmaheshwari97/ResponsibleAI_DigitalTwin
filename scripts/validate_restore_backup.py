from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from services.config_service import get_setting
from services.docker_cli_service import DockerCliUnavailable, docker_command


load_dotenv()

CHECK_TABLES = (
    "simulation_runs",
    "audit_events",
    "policy_rules",
    "twin_snapshots",
)


def _run(command: list[str], *, input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def _text(result: subprocess.CompletedProcess) -> str:
    return result.stdout.decode("utf-8", errors="replace").strip()


def _latest_backup(backup_dir: Path) -> Path:
    backups = sorted(
        backup_dir.glob("*.sql.gz"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not backups:
        raise SystemExit(
            f"No .sql.gz backup found in {backup_dir}. Run python scripts/backup_database.py first."
        )
    return backups[0]


def _scalar(container: str, user: str, database: str, sql: str) -> str:
    result = _run(
        docker_command(
            "exec",
            container,
            "psql",
            "-U",
            user,
            "-d",
            database,
            "-Atc",
            sql,
        )
    )
    return _text(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Non-destructively validate the latest PostgreSQL backup by restoring it "
            "into a temporary database inside the existing PostgreSQL container."
        )
    )
    parser.add_argument(
        "--backup",
        type=Path,
        default=None,
        help="Optional .sql.gz backup path. Defaults to the newest file in BACKUP_DIR.",
    )
    args = parser.parse_args()

    container = get_setting("POSTGRES_CONTAINER", "rai-postgres")
    source_db = get_setting("POSTGRES_DB", "rai_twin")
    user = get_setting("POSTGRES_USER", "rai_user")
    backup_dir = Path(get_setting("BACKUP_DIR", "backups") or "backups")
    if not backup_dir.is_absolute():
        backup_dir = PROJECT_ROOT / backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup = args.backup or _latest_backup(backup_dir)
    if not backup.is_absolute():
        backup = (PROJECT_ROOT / backup).resolve()
    if not backup.exists():
        raise SystemExit(f"Backup not found: {backup}")

    try:
        docker_command("version")
    except DockerCliUnavailable as exc:
        raise SystemExit(str(exc)) from exc

    sql_bytes = gzip.decompress(backup.read_bytes())
    if not sql_bytes:
        raise SystemExit("Backup decompresses to an empty SQL payload.")

    temp_db = f"rai_restore_check_{uuid4().hex[:10]}"
    marker = backup_dir / "restore_validation.json"
    created = False

    print("Responsible AI Digital Twin - Isolated Restore Validation")
    print("=" * 72)
    print(f"Backup:     {backup}")
    print(f"Source DB:  {source_db}")
    print(f"Temp DB:    {temp_db}")
    print("The source database is not modified.")

    try:
        _run(
            docker_command(
                "exec",
                container,
                "createdb",
                "-U",
                user,
                temp_db,
            )
        )
        created = True

        print(f"> Restoring backup into temporary database {temp_db}")
        restore_result = _run(
            docker_command(
                "exec",
                "-i",
                container,
                "psql",
                "-U",
                user,
                "-d",
                temp_db,
            ),
            input_bytes=sql_bytes,
        )

        source_counts: dict[str, int] = {}
        restored_counts: dict[str, int] = {}

        for table in CHECK_TABLES:
            source_count = int(_scalar(container, user, source_db, f"SELECT COUNT(*) FROM {table};"))
            restored_count = int(_scalar(container, user, temp_db, f"SELECT COUNT(*) FROM {table};"))
            source_counts[table] = source_count
            restored_counts[table] = restored_count
            state = "PASS" if source_count == restored_count else "FAIL"
            print(
                f"[{state}] {table}: source={source_count}, restored={restored_count}"
            )

        schema_count = int(
            _scalar(
                container,
                user,
                temp_db,
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';",
            )
        )
        alembic_version = _scalar(
            container,
            user,
            temp_db,
            "SELECT version_num FROM alembic_version LIMIT 1;",
        )

        counts_match = source_counts == restored_counts
        schema_ok = schema_count >= 10
        alembic_ok = alembic_version == "005_twin_snapshots"

        print(f"[{'PASS' if schema_ok else 'FAIL'}] public tables: {schema_count}")
        print(
            f"[{'PASS' if alembic_ok else 'FAIL'}] Alembic version: {alembic_version or 'missing'}"
        )

        if not (counts_match and schema_ok and alembic_ok):
            raise SystemExit("ISOLATED RESTORE VALIDATION: FAIL")

        payload = {
            "status": "PASS",
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "backup": str(backup),
            "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
            "source_database": source_db,
            "temporary_database": temp_db,
            "alembic_version": alembic_version,
            "public_table_count": schema_count,
            "source_counts": source_counts,
            "restored_counts": restored_counts,
        }
        marker.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        print("ISOLATED RESTORE VALIDATION: PASS")
        print(f"Marker written: {marker}")

    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(
            "ISOLATED RESTORE VALIDATION: FAIL"
            + (f"\n{detail}" if detail else "")
        ) from exc
    finally:
        if created:
            print(f"> Removing temporary database {temp_db}")
            subprocess.run(
                docker_command(
                    "exec",
                    container,
                    "dropdb",
                    "-U",
                    user,
                    "--if-exists",
                    temp_db,
                ),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )


if __name__ == "__main__":
    main()
