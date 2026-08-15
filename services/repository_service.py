from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import select

from models.database_models import (
    AgentEventRecord, AuditEventRecord, FindingRecord, HumanDecisionRecord,
    PolicyDecisionRecord, PolicyRuleResultRecord, RemediationRecord,
    SecurityTestRecord, SimulationRunRecord, TwinSnapshotRecord,
)
from models.workflow_models import FindingAnalysis, PolicyDecision, RemediationPlan, SimulationRun
from services.database_service import get_database_session


def _enum_value(value):
    if isinstance(value, Enum):
        return value.value
    return getattr(value, "value", value)


def _parse_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def save_run(run: SimulationRun) -> None:
    with get_database_session() as db:
        record = db.get(SimulationRunRecord, run.run_id)
        values = {
            "scenario_id": run.scenario_id,
            "scenario_name": run.scenario_name,
            "objective": run.objective,
            "status": _enum_value(run.status),
            "model_name": run.model_name,
            "initial_twin_version": run.initial_twin_version,
            "final_twin_version": run.final_twin_version,
            "started_at": _parse_datetime(run.started_at),
            "completed_at": _parse_datetime(run.completed_at),
            "result": run.result,
            "last_transition_at": _parse_datetime(run.last_transition_at),
            "failure_reason": run.failure_reason,
            "interrupted_at": _parse_datetime(run.interrupted_at),
            "abort_reason": run.abort_reason,
        }
        if record is None:
            db.add(SimulationRunRecord(run_id=run.run_id, **values))
        else:
            for key, value in values.items():
                setattr(record, key, value)
        db.commit()


def save_security_test(run_id: str, stage: str, result: dict) -> None:
    with get_database_session() as db:
        stmt = select(SecurityTestRecord).where(SecurityTestRecord.run_id == run_id, SecurityTestRecord.stage == stage)
        record = db.scalars(stmt).first()
        values = {
            "scenario": result["scenario"],
            "requesting_user": result["requesting_user"],
            "resource_id": result["resource_id"],
            "expected_owner": result.get("expected_owner"),
            "observed_owner": result.get("observed_owner"),
            "expected_status": result["expected_status"],
            "observed_status": result["observed_status"],
            "access_granted": result["access_granted"],
            "vulnerability_detected": result["vulnerability_detected"],
            "response_json": result["response"],
            "result": result["result"],
        }
        if record is None:
            db.add(SecurityTestRecord(run_id=run_id, stage=stage, **values))
        else:
            for key, value in values.items(): setattr(record, key, value)
        db.commit()


def save_finding(run_id: str, finding: FindingAnalysis) -> None:
    classification = finding.classification
    component = _enum_value(finding.affected_component)
    with get_database_session() as db:
        stmt = select(FindingRecord).where(FindingRecord.run_id == run_id, FindingRecord.classification == classification, FindingRecord.affected_component == component)
        record = db.scalars(stmt).first()
        values = {
            "severity": _enum_value(finding.severity),
            "confidence_level": _enum_value(finding.confidence),
            "root_cause": finding.root_cause,
            "security_impact": finding.security_impact,
            "recommended_action": finding.recommended_action,
        }
        if record is None:
            db.add(FindingRecord(run_id=run_id, classification=classification, affected_component=component, **values))
        else:
            for key, value in values.items(): setattr(record, key, value)
        db.commit()


def save_remediation(run_id: str, remediation: RemediationPlan) -> None:
    with get_database_session() as db:
        db.merge(RemediationRecord(
            remediation_id=remediation.remediation_id,
            run_id=run_id,
            title=remediation.title,
            target_component=_enum_value(remediation.target_component),
            action_type=remediation.action_type,
            proposed_change=remediation.proposed_change,
            risk=_enum_value(remediation.risk),
            expected_security_benefit=remediation.expected_security_benefit,
            possible_side_effects=list(remediation.possible_side_effects),
            verification_test=remediation.verification_test,
            requires_human_approval=remediation.requires_human_approval,
            target_environment=remediation.target_environment,
        ))
        db.commit()


def save_human_decision(run_id: str, remediation_id: str | None, decision: str, actor: str = "Human Reviewer") -> None:
    with get_database_session() as db:
        stmt = select(HumanDecisionRecord).where(HumanDecisionRecord.run_id == run_id, HumanDecisionRecord.decision == decision)
        if remediation_id is not None:
            stmt = stmt.where(HumanDecisionRecord.remediation_id == remediation_id)
        if db.scalars(stmt).first() is None:
            db.add(HumanDecisionRecord(run_id=run_id, remediation_id=remediation_id, decision=decision, actor=actor))
            db.commit()


def save_policy_decision(run_id: str, decision: PolicyDecision) -> None:
    with get_database_session() as db:
        db.merge(PolicyDecisionRecord(
            decision_id=decision.decision_id,
            run_id=run_id,
            action=decision.action,
            target=decision.target,
            environment=decision.environment,
            outcome=_enum_value(decision.outcome),
            reason=decision.reason,
            requires_human_approval=decision.requires_human_approval,
            controls_json=[c.model_dump(mode="json") for c in decision.controls],
            decided_at=_parse_datetime(decision.decided_at),
        ))
        db.commit()


def save_agent_event(run_id: str, agent: str, action: str, status: str, event_type: str) -> None:
    with get_database_session() as db:
        db.add(AgentEventRecord(run_id=run_id, agent=agent, action=action, status=_enum_value(status), event_type=_enum_value(event_type)))
        db.commit()


def save_audit_event(run_id: str | None, actor: str, category: str, action: str, status: str, details: str) -> str:
    with get_database_session() as db:
        record = AuditEventRecord(run_id=run_id, actor=actor, category=_enum_value(category), action=action, status=_enum_value(status), details=details)
        db.add(record); db.commit(); db.refresh(record); return record.id


def list_runs(limit: int = 100) -> list[SimulationRunRecord]:
    with get_database_session() as db:
        return list(db.scalars(select(SimulationRunRecord).order_by(SimulationRunRecord.started_at.desc()).limit(limit)).all())


def get_run_record(run_id: str) -> SimulationRunRecord | None:
    with get_database_session() as db: return db.get(SimulationRunRecord, run_id)


def update_run_lifecycle(run_id: str, *, status: str, failure_reason: str | None = None, interrupted_at: datetime | None = None, abort_reason: str | None = None) -> None:
    with get_database_session() as db:
        record = db.get(SimulationRunRecord, run_id)
        if record is None: return
        record.status = status
        record.last_transition_at = datetime.now(timezone.utc)
        record.failure_reason = failure_reason
        record.interrupted_at = interrupted_at
        record.abort_reason = abort_reason
        if status in {"secured", "failed", "rejected", "interrupted", "aborted"}:
            record.completed_at = record.completed_at or datetime.now(timezone.utc)
        db.commit()


def list_security_tests(run_id: str):
    with get_database_session() as db: return list(db.scalars(select(SecurityTestRecord).where(SecurityTestRecord.run_id == run_id).order_by(SecurityTestRecord.created_at.asc())).all())

def list_findings(run_id: str):
    with get_database_session() as db: return list(db.scalars(select(FindingRecord).where(FindingRecord.run_id == run_id).order_by(FindingRecord.created_at.asc())).all())

def list_remediations(run_id: str):
    with get_database_session() as db: return list(db.scalars(select(RemediationRecord).where(RemediationRecord.run_id == run_id).order_by(RemediationRecord.created_at.asc())).all())

def list_human_decisions(run_id: str):
    with get_database_session() as db: return list(db.scalars(select(HumanDecisionRecord).where(HumanDecisionRecord.run_id == run_id).order_by(HumanDecisionRecord.created_at.asc())).all())

def list_policy_decisions(run_id: str):
    with get_database_session() as db: return list(db.scalars(select(PolicyDecisionRecord).where(PolicyDecisionRecord.run_id == run_id).order_by(PolicyDecisionRecord.decided_at.asc())).all())

def list_policy_rule_results(run_id: str):
    with get_database_session() as db: return list(db.scalars(select(PolicyRuleResultRecord).where(PolicyRuleResultRecord.run_id == run_id).order_by(PolicyRuleResultRecord.evaluated_at.asc())).all())

def list_agent_events(run_id: str):
    with get_database_session() as db: return list(db.scalars(select(AgentEventRecord).where(AgentEventRecord.run_id == run_id).order_by(AgentEventRecord.created_at.asc())).all())

def list_audit_events(run_id: str | None = None, limit: int = 1000):
    with get_database_session() as db:
        stmt = select(AuditEventRecord)
        if run_id: stmt = stmt.where(AuditEventRecord.run_id == run_id)
        return list(db.scalars(stmt.order_by(AuditEventRecord.created_at.desc()).limit(limit)).all())

def list_twin_snapshots(run_id: str):
    with get_database_session() as db: return list(db.scalars(select(TwinSnapshotRecord).where(TwinSnapshotRecord.run_id == run_id).order_by(TwinSnapshotRecord.created_at.asc())).all())
