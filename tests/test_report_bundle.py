from __future__ import annotations

import hashlib
import io
import json
import zipfile

import pytest

pytest.importorskip("psycopg")

from services.report_service import evidence_bundle_zip_bytes, evidence_manifest


def _sample_report() -> dict:
    return {
        "run": {
            "run_id": "RUN-TEST-001",
            "scenario_id": "SCN-001",
            "scenario": "Unauthorized Private Message Access",
            "objective": "Controlled local synthetic validation",
            "status": "secured",
            "result": "PASS",
            "model": "fallback",
            "initial_twin_version": "1.0",
            "final_twin_version": "1.1",
            "started_at": "2026-08-15T10:00:00+00:00",
            "completed_at": "2026-08-15T10:00:05+00:00",
            "failure_reason": None,
            "abort_reason": None,
        },
        "security_tests": [],
        "findings": [],
        "remediations": [],
        "human_decisions": [],
        "policy_decisions": [],
        "policy_rule_results": [],
        "twin": {"before": None, "after": None, "snapshots": []},
        "agent_events": [],
        "audit_events": [],
        "timeline": [],
        "integrity": {"valid": True, "reason": "test"},
    }


def test_evidence_zip_contains_manifest_and_verified_hashes():
    report = _sample_report()
    payload = evidence_bundle_zip_bytes(report)

    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        names = set(archive.namelist())
        prefix = "RUN-TEST-001/"
        expected = {
            prefix + "manifest.json",
            prefix + "evidence.json",
            prefix + "timeline.csv",
            prefix + "policy_rules.csv",
            prefix + "audit.csv",
            prefix + "report.pdf",
        }
        assert expected.issubset(names)

        manifest = json.loads(archive.read(prefix + "manifest.json"))
        for item in manifest["files"]:
            body = archive.read(prefix + item["path"])
            assert len(body) == item["bytes"]
            assert hashlib.sha256(body).hexdigest() == item["sha256"]


def test_manifest_exposes_run_identity():
    report = _sample_report()
    manifest = evidence_manifest(report)
    assert manifest["run_id"] == "RUN-TEST-001"
    assert manifest["scenario_id"] == "SCN-001"
    assert manifest["run_result"] == "PASS"
