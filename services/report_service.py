from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from services.evidence_service import verify_hash_chain
from services.repository_service import (
    get_run_record,
    list_agent_events,
    list_audit_events,
    list_findings,
    list_human_decisions,
    list_policy_decisions,
    list_policy_rule_results,
    list_remediations,
    list_security_tests,
    list_twin_snapshots,
)


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def build_run_report(run_id: str) -> dict:
    run = get_run_record(run_id)
    if run is None:
        raise KeyError(f"Unknown run: {run_id}")

    tests = list_security_tests(run_id)
    findings = list_findings(run_id)
    remediations = list_remediations(run_id)
    human = list_human_decisions(run_id)
    policies = list_policy_decisions(run_id)
    rules = list_policy_rule_results(run_id)
    snapshots = list_twin_snapshots(run_id)
    agents = list_agent_events(run_id)
    audits = list_audit_events(run_id, limit=5000)
    integrity = verify_hash_chain(run_id)

    timeline = []
    for test in tests:
        timeline.append(
            {
                "time": _iso(test.created_at),
                "type": "security_test",
                "actor": "Security Testing Agent" if test.stage == "initial" else "Verification Agent",
                "event": f"{test.stage.title()} HTTP test: expected {test.expected_status}, observed {test.observed_status}",
                "status": test.result,
            }
        )
    for finding in findings:
        timeline.append(
            {
                "time": _iso(finding.created_at),
                "type": "finding",
                "actor": "Security Analyst",
                "event": finding.classification,
                "status": finding.severity,
            }
        )
    for remediation in remediations:
        timeline.append(
            {
                "time": _iso(remediation.created_at),
                "type": "remediation",
                "actor": "Remediation Agent",
                "event": remediation.title,
                "status": remediation.risk,
            }
        )
    for decision in human:
        timeline.append(
            {
                "time": _iso(decision.created_at),
                "type": "human_decision",
                "actor": decision.actor,
                "event": f"Human decision: {decision.decision}",
                "status": decision.decision,
            }
        )
    for policy in policies:
        timeline.append(
            {
                "time": _iso(policy.decided_at),
                "type": "policy_decision",
                "actor": "Policy Engine",
                "event": f"{policy.action}: {policy.outcome}",
                "status": policy.outcome,
            }
        )
    for agent in agents:
        timeline.append(
            {
                "time": _iso(agent.created_at),
                "type": "agent_event",
                "actor": agent.agent,
                "event": agent.action,
                "status": agent.status,
            }
        )
    timeline.sort(key=lambda row: row.get("time") or "")

    before_snapshot = snapshots[0].state_json if snapshots else None
    after_snapshot = snapshots[-1].state_json if snapshots else None

    return {
        "run": {
            "run_id": run.run_id,
            "scenario_id": run.scenario_id,
            "scenario": run.scenario_name,
            "objective": run.objective,
            "status": run.status,
            "result": run.result,
            "model": run.model_name,
            "initial_twin_version": run.initial_twin_version,
            "final_twin_version": run.final_twin_version,
            "started_at": _iso(run.started_at),
            "completed_at": _iso(run.completed_at),
            "failure_reason": run.failure_reason,
            "abort_reason": run.abort_reason,
        },
        "security_tests": [
            {
                "stage": test.stage,
                "scenario": test.scenario,
                "requester": test.requesting_user,
                "resource": test.resource_id,
                "expected_owner": test.expected_owner,
                "observed_owner": test.observed_owner,
                "expected_status": test.expected_status,
                "observed_status": test.observed_status,
                "access_granted": test.access_granted,
                "vulnerability_detected": test.vulnerability_detected,
                "result": test.result,
                "response": test.response_json,
                "created_at": _iso(test.created_at),
            }
            for test in tests
        ],
        "findings": [
            {
                "classification": item.classification,
                "severity": item.severity,
                "confidence": item.confidence_level,
                "affected_component": item.affected_component,
                "root_cause": item.root_cause,
                "security_impact": item.security_impact,
                "recommended_action": item.recommended_action,
                "created_at": _iso(item.created_at),
            }
            for item in findings
        ],
        "remediations": [
            {
                "remediation_id": item.remediation_id,
                "title": item.title,
                "target_component": item.target_component,
                "action_type": item.action_type,
                "proposed_change": item.proposed_change,
                "risk": item.risk,
                "expected_security_benefit": item.expected_security_benefit,
                "possible_side_effects": item.possible_side_effects,
                "verification_test": item.verification_test,
                "requires_human_approval": item.requires_human_approval,
                "target_environment": item.target_environment,
                "created_at": _iso(item.created_at),
            }
            for item in remediations
        ],
        "human_decisions": [
            {
                "decision": item.decision,
                "actor": item.actor,
                "remediation_id": item.remediation_id,
                "created_at": _iso(item.created_at),
            }
            for item in human
        ],
        "policy_decisions": [
            {
                "decision_id": item.decision_id,
                "action": item.action,
                "target": item.target,
                "environment": item.environment,
                "outcome": item.outcome,
                "reason": item.reason,
                "requires_human_approval": item.requires_human_approval,
                "controls": item.controls_json,
                "decided_at": _iso(item.decided_at),
            }
            for item in policies
        ],
        "policy_rule_results": [
            {
                "decision_id": item.decision_id,
                "rule_id": item.rule_id,
                "status": item.status,
                "passed": item.passed,
                "evidence": item.evidence,
                "evaluated_at": _iso(item.evaluated_at),
            }
            for item in rules
        ],
        "twin": {
            "before": before_snapshot,
            "after": after_snapshot,
            "snapshots": [
                {
                    "snapshot_id": item.snapshot_id,
                    "version": item.twin_version,
                    "phase": item.phase,
                    "trigger": item.trigger,
                    "state_hash": item.state_hash,
                    "state": item.state_json,
                    "created_at": _iso(item.created_at),
                }
                for item in snapshots
            ],
        },
        "agent_events": [
            {
                "agent": item.agent,
                "action": item.action,
                "status": item.status,
                "event_type": item.event_type,
                "created_at": _iso(item.created_at),
            }
            for item in agents
        ],
        "audit_events": [
            {
                "sequence": item.sequence_number,
                "actor": item.actor,
                "category": item.category,
                "action": item.action,
                "status": item.status,
                "details": item.details,
                "event_hash": item.event_hash,
                "previous_hash": item.previous_hash,
                "created_at": _iso(item.created_at),
            }
            for item in sorted(audits, key=lambda x: x.created_at)
        ],
        "timeline": timeline,
        "integrity": integrity,
    }


def report_json_bytes(report: dict) -> bytes:
    return json.dumps(report, indent=2, default=str).encode("utf-8")


def timeline_csv_bytes(report: dict) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["time", "type", "actor", "event", "status"],
    )
    writer.writeheader()
    writer.writerows(report.get("timeline", []))
    return buffer.getvalue().encode("utf-8-sig")


def policy_csv_bytes(report: dict) -> bytes:
    buffer = io.StringIO()
    fieldnames = [
        "decision_id",
        "rule_id",
        "status",
        "passed",
        "evidence",
        "evaluated_at",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(report.get("policy_rule_results", []))
    return buffer.getvalue().encode("utf-8-sig")


def audit_csv_bytes(report: dict) -> bytes:
    buffer = io.StringIO()
    fieldnames = [
        "sequence",
        "created_at",
        "actor",
        "category",
        "action",
        "status",
        "details",
        "previous_hash",
        "event_hash",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(report.get("audit_events", []))
    return buffer.getvalue().encode("utf-8-sig")


def report_pdf_bytes(report: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Responsible AI Digital Twin Evidence - {report['run']['run_id']}",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CenteredTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    story = [
        Paragraph("Responsible AI Digital Twin Evidence Report", styles["CenteredTitle"]),
        Paragraph(escape(report["run"]["run_id"]), styles["Heading2"]),
        Spacer(1, 6),
    ]

    summary_rows = [
        ["Scenario", report["run"]["scenario"]],
        ["Status", report["run"]["status"]],
        ["Result", report["run"].get("result") or "-"],
        ["Model", report["run"].get("model") or "fallback"],
        [
            "Twin",
            f"{report['run']['initial_twin_version']} -> "
            f"{report['run'].get('final_twin_version') or '—'}",
        ],
        ["Started", report["run"].get("started_at") or "-"],
        ["Completed", report["run"].get("completed_at") or "-"],
        [
            "Evidence integrity",
            "VALID" if report.get("integrity", {}).get("valid") else "NOT VERIFIED",
        ],
    ]
    summary = Table(summary_rows, colWidths=[42 * mm, 122 * mm])
    summary.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ]
        )
    )
    story.extend([summary, Spacer(1, 12)])

    story.append(Paragraph("HTTP Evidence", styles["Heading2"]))
    test_rows = [["Stage", "Requester", "Resource", "Expected", "Observed", "Result"]]
    for test in report.get("security_tests", []):
        test_rows.append(
            [
                test["stage"],
                test["requester"],
                test["resource"],
                str(test["expected_status"]),
                str(test["observed_status"]),
                test["result"],
            ]
        )
    if len(test_rows) == 1:
        test_rows.append(["-", "-", "-", "-", "-", "No evidence"])
    table = Table(test_rows, repeatRows=1, colWidths=[20*mm, 27*mm, 45*mm, 20*mm, 20*mm, 20*mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ]
        )
    )
    story.extend([table, Spacer(1, 12)])

    if report.get("findings"):
        finding = report["findings"][-1]
        story.append(Paragraph("Structured Finding", styles["Heading2"]))
        for label, value in [
            ("Classification", finding["classification"]),
            ("Severity", finding["severity"]),
            ("Affected component", finding["affected_component"]),
            ("Root cause", finding["root_cause"]),
            ("Security impact", finding["security_impact"]),
            ("Recommended action", finding["recommended_action"]),
        ]:
            story.append(
                Paragraph(f"<b>{escape(label)}:</b> {escape(str(value))}", styles["BodyText"])
            )
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 8))

    if report.get("remediations"):
        remediation = report["remediations"][-1]
        story.append(Paragraph("Remediation & Human Oversight", styles["Heading2"]))
        story.append(
            Paragraph(
                f"<b>{escape(remediation['title'])}</b><br/>{escape(remediation['proposed_change'])}",
                styles["BodyText"],
            )
        )
        human_text = ", ".join(
            f"{item['actor']}: {item['decision']}" for item in report.get("human_decisions", [])
        ) or "No human decision recorded"
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Human decision:</b> {escape(human_text)}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Policy Evidence", styles["Heading2"]))
    policy_rows = [["Rule", "Status", "Passed", "Evidence"]]
    for item in report.get("policy_rule_results", []):
        policy_rows.append(
            [
                item["rule_id"],
                item["status"],
                str(item["passed"]),
                Paragraph(escape(str(item["evidence"])), styles["BodyText"]),
            ]
        )
    if len(policy_rows) == 1:
        policy_rows.append(["-", "-", "-", "No policy evidence"])
    policy_table = Table(policy_rows, repeatRows=1, colWidths=[25*mm, 22*mm, 18*mm, 99*mm])
    policy_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([policy_table, PageBreak()])

    story.append(Paragraph("Evidence Timeline", styles["Heading2"]))
    timeline_rows = [["Time", "Type", "Actor", "Event", "Status"]]
    for item in report.get("timeline", []):
        timeline_rows.append(
            [
                item.get("time") or "-",
                item.get("type") or "-",
                item.get("actor") or "-",
                Paragraph(escape(str(item.get("event") or "-")), styles["BodyText"]),
                item.get("status") or "-",
            ]
        )
    timeline_table = Table(
        timeline_rows,
        repeatRows=1,
        colWidths=[34*mm, 25*mm, 31*mm, 62*mm, 20*mm],
    )
    timeline_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
            ]
        )
    )
    story.append(timeline_table)
    doc.build(story)
    return buffer.getvalue()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def evidence_bundle_payloads(report: dict) -> dict[str, bytes]:
    return {
        "evidence.json": report_json_bytes(report),
        "timeline.csv": timeline_csv_bytes(report),
        "policy_rules.csv": policy_csv_bytes(report),
        "audit.csv": audit_csv_bytes(report),
        "report.pdf": report_pdf_bytes(report),
    }


def evidence_manifest(report: dict, payloads: dict[str, bytes] | None = None) -> dict:
    payloads = payloads or evidence_bundle_payloads(report)
    return {
        "manifest_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": report["run"]["run_id"],
        "scenario_id": report["run"].get("scenario_id"),
        "run_status": report["run"].get("status"),
        "run_result": report["run"].get("result"),
        "evidence_integrity": report.get("integrity", {}),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": _sha256_bytes(payload),
            }
            for name, payload in sorted(payloads.items())
        ],
    }


def evidence_manifest_bytes(
    report: dict, payloads: dict[str, bytes] | None = None
) -> bytes:
    payloads = payloads or evidence_bundle_payloads(report)
    manifest = evidence_manifest(report, payloads)
    return json.dumps(manifest, indent=2, default=str).encode("utf-8")


def evidence_bundle_zip_bytes(
    report: dict, payloads: dict[str, bytes] | None = None
) -> bytes:
    buffer = io.BytesIO()
    run_id = report["run"]["run_id"]
    payloads = payloads or evidence_bundle_payloads(report)
    manifest = evidence_manifest(report, payloads)
    manifest_bytes = json.dumps(manifest, indent=2, default=str).encode("utf-8")

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{run_id}/manifest.json", manifest_bytes)
        for name, payload in payloads.items():
            archive.writestr(f"{run_id}/{name}", payload)
    return buffer.getvalue()
