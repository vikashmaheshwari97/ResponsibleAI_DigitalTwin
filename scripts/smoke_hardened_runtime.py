from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
import urllib3

from services.docker_cli_service import DockerCliUnavailable, docker_command


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _docker_port(container: str) -> tuple[bool | None, str]:
    try:
        command = docker_command("port", container)
    except DockerCliUnavailable as exc:
        return None, str(exc)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "container unavailable").strip()

    output = result.stdout.strip()
    if output:
        return False, f"Unexpected published port(s): {output}"
    return True, "No host-published ports."


def _container_running(container: str) -> tuple[bool | None, str]:
    try:
        command = docker_command("inspect", "-f", "{{.State.Running}}", container)
    except DockerCliUnavailable as exc:
        return None, str(exc)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "container unavailable").strip()

    running = result.stdout.strip().lower() == "true"
    return running, "running" if running else "not running"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test the local production-style HTTPS runtime after "
            "docker compose -f docker-compose.prod.yml up -d --build."
        )
    )
    parser.add_argument(
        "--base-url",
        default="https://localhost:8443",
        help="HTTPS base URL for the local reverse proxy.",
    )
    args = parser.parse_args()

    checks: list[tuple[str, bool, str]] = []

    try:
        health = requests.get(
            f"{args.base_url.rstrip('/')}/_stcore/health",
            timeout=10,
            verify=False,
        )
        checks.append(
            (
                "HTTPS Streamlit health",
                health.status_code == 200,
                f"HTTP {health.status_code}",
            )
        )
    except Exception as exc:
        checks.append(("HTTPS Streamlit health", False, str(exc)))

    try:
        response = requests.get(args.base_url, timeout=10, verify=False)
        required_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": "SAMEORIGIN",
            "referrer-policy": "no-referrer",
        }
        missing = []
        for name, expected in required_headers.items():
            actual = response.headers.get(name)
            if actual != expected:
                missing.append(f"{name}={actual!r}")

        checks.append(
            (
                "Reverse-proxy security headers",
                response.status_code == 200 and not missing,
                "HTTP 200 and required headers present"
                if not missing and response.status_code == 200
                else (
                    f"HTTP {response.status_code}; missing/mismatched: "
                    f"{', '.join(missing) or 'none'}"
                ),
            )
        )
    except Exception as exc:
        checks.append(("Reverse-proxy security headers", False, str(exc)))

    for container in (
        "rai-app",
        "rai-nginx",
        "rai-postgres-prod",
        "rai-secure-messenger-prod",
    ):
        running, detail = _container_running(container)
        checks.append((f"Container running: {container}", running is True, detail))

    for container in ("rai-postgres-prod", "rai-secure-messenger-prod"):
        private, detail = _docker_port(container)
        checks.append((f"No host port: {container}", private is True, detail))

    print("Responsible AI Digital Twin - Hardened Runtime Smoke Test")
    print("=" * 72)
    for name, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        print(f"       {detail}")

    failures = [name for name, passed, _ in checks if not passed]
    print("\nResult")
    print("=" * 72)

    if failures:
        print("HARDENED RUNTIME SMOKE TEST: FAIL")
        print("Failed checks: " + ", ".join(failures))
        raise SystemExit(1)

    print("HARDENED RUNTIME SMOKE TEST: PASS")
    print(
        "This validates the local production-style profile only; "
        "it is not UT deployment."
    )


if __name__ == "__main__":
    main()
