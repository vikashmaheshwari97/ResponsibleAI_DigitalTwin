from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from sqlalchemy import inspect


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.database_service import engine  # noqa: E402


CORE_TABLES = {
    "simulation_runs",
    "security_tests",
    "findings",
    "remediations",
    "human_decisions",
    "policy_decisions",
    "agent_events",
    "audit_events",
}


def run_alembic(*args: str) -> None:
    cmd = [sys.executable, "-m", "alembic", *args]
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))


def main() -> None:
    tables = set(inspect(engine).get_table_names())
    has_alembic = "alembic_version" in tables
    has_core = CORE_TABLES.issubset(tables)

    if not tables:
        print("Empty database detected; applying all migrations.")
        run_alembic("upgrade", "head")
    elif not has_alembic and has_core:
        print("Existing Phase-10A schema detected; baselining at 001_initial_schema.")
        run_alembic("stamp", "001_initial_schema")
        run_alembic("upgrade", "head")
    elif has_alembic:
        print("Alembic-managed database detected; upgrading to head.")
        run_alembic("upgrade", "head")
    else:
        print("Unexpected database schema; refusing destructive migration.")
        print("Tables:", ", ".join(sorted(tables)))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
