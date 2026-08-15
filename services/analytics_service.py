from __future__ import annotations

from collections import defaultdict
from datetime import datetime

PASS_STATUSES = {"secured", "validated"}
INTERRUPTED_STATUSES = {"interrupted", "aborted"}


def duration_seconds(started_at: datetime | None, completed_at: datetime | None) -> float | None:
    if not started_at or not completed_at:
        return None
    return max(0.0, (completed_at - started_at).total_seconds())


def _pct(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 1) if denominator else 0.0


def collect_run_analytics(limit: int = 1000) -> dict:
    from services.repository_service import (
        list_human_decisions,
        list_policy_decisions,
        list_runs,
        list_security_tests,
    )

    runs = list_runs(limit=limit)

    total = len(runs)
    pass_runs = sum(
        1 for run in runs if run.result == "PASS" or run.status in PASS_STATUSES
    )
    fail_runs = sum(
        1 for run in runs if run.result == "FAIL" or run.status == "failed"
    )
    interrupted_runs = sum(1 for run in runs if run.status in INTERRUPTED_STATUSES)
    rejected_runs = sum(1 for run in runs if run.status == "rejected")

    durations = [
        value
        for run in runs
        if (value := duration_seconds(run.started_at, run.completed_at)) is not None
    ]
    average_duration = round(sum(durations) / len(durations), 1) if durations else 0.0

    verification_runs = 0
    policy_block_runs = 0
    approved_decisions = 0
    rejected_decisions = 0

    per_scenario = defaultdict(
        lambda: {
            "scenario_id": "",
            "scenario": "",
            "total": 0,
            "pass": 0,
            "fail": 0,
            "interrupted": 0,
            "verified": 0,
            "durations": [],
        }
    )
    per_day = defaultdict(lambda: {"total": 0, "pass": 0, "fail": 0})

    for run in runs:
        tests = list_security_tests(run.run_id)
        policies = list_policy_decisions(run.run_id)
        humans = list_human_decisions(run.run_id)

        verified = any(test.stage == "verification" for test in tests)
        if verified:
            verification_runs += 1
        if any(policy.outcome == "BLOCK" for policy in policies):
            policy_block_runs += 1

        approved_decisions += sum(1 for decision in humans if decision.decision == "approved")
        rejected_decisions += sum(1 for decision in humans if decision.decision == "rejected")

        item = per_scenario[run.scenario_id]
        item["scenario_id"] = run.scenario_id
        item["scenario"] = run.scenario_name
        item["total"] += 1
        if run.result == "PASS" or run.status in PASS_STATUSES:
            item["pass"] += 1
        if run.result == "FAIL" or run.status == "failed":
            item["fail"] += 1
        if run.status in INTERRUPTED_STATUSES:
            item["interrupted"] += 1
        if verified:
            item["verified"] += 1
        dur = duration_seconds(run.started_at, run.completed_at)
        if dur is not None:
            item["durations"].append(dur)

        day = run.started_at.date().isoformat()
        per_day[day]["total"] += 1
        if run.result == "PASS" or run.status in PASS_STATUSES:
            per_day[day]["pass"] += 1
        if run.result == "FAIL" or run.status == "failed":
            per_day[day]["fail"] += 1

    scenario_rows = []
    for _, item in sorted(per_scenario.items()):
        scenario_rows.append(
            {
                "Scenario ID": item["scenario_id"],
                "Scenario": item["scenario"],
                "Runs": item["total"],
                "Pass": item["pass"],
                "Fail": item["fail"],
                "Interrupted": item["interrupted"],
                "Pass Rate %": _pct(item["pass"], item["total"]),
                "Verification Rate %": _pct(item["verified"], item["total"]),
                "Avg Duration (s)": (
                    round(sum(item["durations"]) / len(item["durations"]), 1)
                    if item["durations"]
                    else 0.0
                ),
            }
        )

    trend_rows = [
        {
            "Date": day,
            "Runs": values["total"],
            "Pass": values["pass"],
            "Fail": values["fail"],
        }
        for day, values in sorted(per_day.items())
    ]

    human_total = approved_decisions + rejected_decisions
    return {
        "total_runs": total,
        "pass_runs": pass_runs,
        "fail_runs": fail_runs,
        "interrupted_runs": interrupted_runs,
        "rejected_runs": rejected_runs,
        "verification_rate": _pct(verification_runs, total),
        "policy_block_rate": _pct(policy_block_runs, total),
        "average_duration_seconds": average_duration,
        "human_approvals": approved_decisions,
        "human_rejections": rejected_decisions,
        "human_approval_rate": _pct(approved_decisions, human_total),
        "scenario_rows": scenario_rows,
        "trend_rows": trend_rows,
        "runs": runs,
    }
