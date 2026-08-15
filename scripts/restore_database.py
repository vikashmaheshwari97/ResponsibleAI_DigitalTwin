from __future__ import annotations

import argparse
import gzip
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from services.config_service import get_setting
from services.docker_cli_service import DockerCliUnavailable, docker_command


load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore a PostgreSQL evidence backup.")
    parser.add_argument("backup", type=Path)
    parser.add_argument(
        "--confirm",
        required=True,
        help="Must be exactly RESTORE to acknowledge destructive replacement.",
    )
    args = parser.parse_args()

    if args.confirm != "RESTORE":
        raise SystemExit("Refusing restore: pass --confirm RESTORE explicitly.")
    if not args.backup.exists():
        raise SystemExit(f"Backup does not exist: {args.backup}")

    container = get_setting("POSTGRES_CONTAINER", "rai-postgres")
    database = get_setting("POSTGRES_DB", "rai_twin")
    user = get_setting("POSTGRES_USER", "rai_user")

    with gzip.open(args.backup, "rb") as handle:
        sql_bytes = handle.read()

    if not sql_bytes:
        raise SystemExit("Backup contains no SQL data; restore aborted.")

    try:
        command = docker_command(
            "exec",
            "-i",
            container,
            "psql",
            "-U",
            user,
            "-d",
            database,
        )
    except DockerCliUnavailable as exc:
        raise SystemExit(str(exc)) from exc

    print(">", " ".join(command))

    try:
        subprocess.run(
            command,
            input=sql_bytes,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(
            "PostgreSQL restore failed while invoking Docker/WSL Docker."
            + (f"\n{detail}" if detail else "")
        ) from exc

    print("Restore completed. Run python scripts/migrate_database.py afterwards.")


if __name__ == "__main__":
    main()
