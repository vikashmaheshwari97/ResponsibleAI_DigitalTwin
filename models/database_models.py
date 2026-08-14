from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


class Base(DeclarativeBase):
    pass


class SimulationRunRecord(Base):
    __tablename__ = "simulation_runs"
    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    initial_twin_version: Mapped[str] = mapped_column(String(50), nullable=False)
    final_twin_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_transition_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    interrupted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    abort_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class SecurityTestRecord(Base):
    __tablename__ = "security_tests"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("TEST"))
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    scenario: Mapped[str] = mapped_column(String(255), nullable=False)
    requesting_user: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observed_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_status: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_status: Mapped[int] = mapped_column(Integer, nullable=False)
    access_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    vulnerability_detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class FindingRecord(Base):
    __tablename__ = "findings"
    finding_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("FIND"))
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    classification: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_component: Mapped[str] = mapped_column(String(255), nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    security_impact: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RemediationRecord(Base):
    __tablename__ = "remediations"
    remediation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_component: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    proposed_change: Mapped[str] = mapped_column(Text, nullable=False)
    risk: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_security_benefit: Mapped[str] = mapped_column(Text, nullable=False)
    possible_side_effects: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    verification_test: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, nullable=False)
    target_environment: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class HumanDecisionRecord(Base):
    __tablename__ = "human_decisions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("HUM"))
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    remediation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="Human Reviewer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PolicyDecisionRecord(Base):
    __tablename__ = "policy_decisions"
    decision_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, nullable=False)
    controls_json: Mapped[list] = mapped_column(JSONB, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentEventRecord(Base):
    __tablename__ = "agent_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("AGENT"))
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditEventRecord(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("AUD"))
    run_id: Mapped[str | None] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    integrity_version: Mapped[str | None] = mapped_column(String(20), nullable=True)


class PolicyRuleRecord(Base):
    __tablename__ = "policy_rules"
    rule_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    effect: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class PolicyRuleResultRecord(Base):
    __tablename__ = "policy_rule_results"
    __table_args__ = (UniqueConstraint("decision_id", "rule_id", name="uq_policy_rule_result_decision_rule"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("PRR"))
    decision_id: Mapped[str] = mapped_column(ForeignKey("policy_decisions.decision_id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("policy_rules.rule_id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class TwinSnapshotRecord(Base):
    __tablename__ = "twin_snapshots"
    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("SNAP"))
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    twin_version: Mapped[str] = mapped_column(String(50), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger: Mapped[str] = mapped_column(String(255), nullable=False)
    state_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


Index("ix_audit_events_run_sequence", AuditEventRecord.run_id, AuditEventRecord.sequence_number)
