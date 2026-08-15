from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.readiness_service import readiness_snapshot  # noqa: E402


def _print_hardening(snapshot: dict) -> None:
    print("Responsible AI Digital Twin - Hardening Validation")
    print("=" * 67)
    for item in snapshot["checks"]:
        if not item["hardening_required"]:
            continue
        marker = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[item["status"]]
        print(f"{marker:7} {item['category']:<20} {item['name']}")
        print(f"        {item['detail']}")
    print(f"\nHardening readiness score: {snapshot['hardening_score']:.1f}%")


def _compose_config_check() -> tuple[bool | None, str]:
    docker = shutil.which("docker")
    if not docker:
        return None, "Docker CLI not found; Compose configuration was not executed."

    command = [
        docker,
        "compose",
        "-f",
        "docker-compose.prod.yml",
        "config",
        "--quiet",
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True, "docker compose -f docker-compose.prod.yml config --quiet passed."
    detail = (result.stderr or result.stdout or "unknown Docker Compose error").strip()
    return False, detail


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the production-style local hardening configuration. This does not "
            "deploy to the University of Tartu server."
        )
    )
    parser.add_argument(
        "--skip-compose",
        action="store_true",
        help="Skip Docker Compose configuration validation.",
    )
    args = parser.parse_args()

    snapshot = readiness_snapshot()
    _print_hardening(snapshot)

    compose_ok: bool | None = None
    if not args.skip_compose:
        compose_ok, compose_detail = _compose_config_check()
        marker = "PASS" if compose_ok is True else ("WARN" if compose_ok is None else "FAIL")
        print(f"\n[{marker}] Docker Compose configuration")
        print(f"       {compose_detail}")

    blockers = list(snapshot["hardening_blockers"])
    if compose_ok is False:
        blockers.append("Docker Compose configuration")

    print("\nResult")
    print("=" * 67)
    if not blockers:
        print("LOCAL HARDENING VALIDATION: PASS")
        print("The project is ready for the local HTTPS production-style smoke test.")
        raise SystemExit(0)

    print("LOCAL HARDENING VALIDATION: INCOMPLETE")
    print("Remaining items: " + ", ".join(blockers))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
