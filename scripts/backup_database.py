from __future__ import annotations

from datetime import datetime, timezone
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
    container = get_setting("POSTGRES_CONTAINER", "rai-postgres")
    database = get_setting("POSTGRES_DB", "rai_twin")
    user = get_setting("POSTGRES_USER", "rai_user")
    backup_dir = Path(get_setting("BACKUP_DIR", "backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"{database}_{stamp}.sql.gz"

    try:
        command = docker_command(
            "exec",
            container,
            "pg_dump",
            "-U",
            user,
            "-d",
            database,
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
        )
    except DockerCliUnavailable as exc:
        raise SystemExit(str(exc)) from exc

    print(">", " ".join(command))

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(
            "PostgreSQL backup failed while invoking Docker/WSL Docker."
            + (f"\n{detail}" if detail else "")
        ) from exc

    if not result.stdout:
        raise SystemExit("PostgreSQL backup returned no SQL output; backup was not written.")

    with gzip.open(destination, "wb") as handle:
        handle.write(result.stdout)

    print(f"Backup written: {destination.resolve()}")
    print(f"Compressed size: {destination.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
