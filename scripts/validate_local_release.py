from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.readiness_service import readiness_snapshot  # noqa: E402
from services.sandbox_service import (  # noqa: E402
    apply_secure_mode,
    configure_sandbox,
    get_sandbox_health,
    reset_sandbox,
)
from services.scenario_registry_service import list_scenarios  # noqa: E402
from services.security_test_service import run_scenario_test  # noqa: E402


def _print_check_table(snapshot: dict) -> None:
    print("\nResponsible AI Digital Twin - Local Release Validation")
    print("=" * 67)
    print(f"Local readiness score:     {snapshot['local_score']:.1f}%")
    print(f"Hardening readiness score: {snapshot['hardening_score']:.1f}%")
    print()
    for item in snapshot["checks"]:
        marker = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[item["status"]]
        print(f"{marker:7} {item['category']:<20} {item['name']}")
        print(f"        {item['detail']}")


def _exercise_sandbox() -> dict:
    original = get_sandbox_health()
    if not original.get("available"):
        return {
            "passed": False,
            "error": f"SecureMessenger unavailable: {original.get('error')}",
            "scenarios": [],
        }

    results = []
    try:
        for scenario in list_scenarios():
            reset_sandbox()
            vulnerable = run_scenario_test(scenario.scenario_id)

            apply_secure_mode()
            secure = run_scenario_test(scenario.scenario_id)

            vulnerable_ok = (
                vulnerable.get("result") == "FAIL"
                and vulnerable.get("vulnerability_detected") is True
            )
            secure_ok = (
                secure.get("result") == "PASS"
                and secure.get("vulnerability_detected") is False
                and secure.get("observed_status") == scenario.expected_status
            )
            results.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "scenario": scenario.name,
                    "vulnerable_observed": vulnerable.get("observed_status"),
                    "vulnerable_result": vulnerable.get("result"),
                    "secure_observed": secure.get("observed_status"),
                    "secure_expected": scenario.expected_status,
                    "secure_result": secure.get("result"),
                    "passed": vulnerable_ok and secure_ok,
                }
            )
    finally:
        try:
            if original.get("security_profile") in {"vulnerable", "secure"}:
                configure_sandbox(
                    original["security_profile"],
                    str(original.get("version") or ("1.1" if original["security_profile"] == "secure" else "1.0")),
                )
            else:
                reset_sandbox()
        except Exception:
            # The validation result should still be visible even if restoration fails.
            pass

    return {
        "passed": bool(results) and all(item["passed"] for item in results),
        "error": None,
        "scenarios": results,
    }


def _print_sandbox_results(matrix: dict) -> None:
    print("\nControlled Scenario Contract Matrix")
    print("=" * 67)
    if matrix.get("error"):
        print(f"[FAIL] {matrix['error']}")
        return
    for item in matrix["scenarios"]:
        marker = "PASS" if item["passed"] else "FAIL"
        print(
            f"[{marker}] {item['scenario_id']} | vulnerable HTTP "
            f"{item['vulnerable_observed']} ({item['vulnerable_result']}) | "
            f"secure HTTP {item['secure_observed']} "
            f"expected {item['secure_expected']} ({item['secure_result']})"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the local feature-complete Responsible AI Digital Twin release "
            "without changing the PostgreSQL schema."
        )
    )
    parser.add_argument(
        "--exercise-sandbox",
        action="store_true",
        help=(
            "Run all four approved HTTP contracts in vulnerable and secure profiles. "
            "The original sandbox profile is restored afterwards."
        ),
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path for the machine-readable validation result.",
    )
    args = parser.parse_args()

    snapshot = readiness_snapshot()
    _print_check_table(snapshot)

    matrix = None
    if args.exercise_sandbox:
        matrix = _exercise_sandbox()
        _print_sandbox_results(matrix)

    result = {
        "readiness": snapshot,
        "sandbox_contract_matrix": matrix,
    }

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nValidation JSON written to: {args.json_out.resolve()}")

    local_ok = not snapshot["local_blockers"]
    matrix_ok = matrix is None or bool(matrix.get("passed"))

    print("\nResult")
    print("=" * 67)
    if local_ok and matrix_ok:
        print("LOCAL RELEASE VALIDATION: PASS")
        raise SystemExit(0)

    print("LOCAL RELEASE VALIDATION: FAIL")
    if snapshot["local_blockers"]:
        print("Blockers: " + ", ".join(snapshot["local_blockers"]))
    if matrix is not None and not matrix_ok:
        print("One or more controlled scenario contracts failed.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
