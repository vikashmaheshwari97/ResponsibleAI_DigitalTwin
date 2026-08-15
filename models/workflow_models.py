from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowModel(BaseModel):
    model_config = ConfigDict(validate_assignment=True, str_strip_whitespace=True)


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TwinComponentName(str, Enum):
    api_gateway = "API Gateway"
    authentication_service = "Authentication Service"
    message_api = "Message API"
    message_database = "Message Database"


class RunStatus(str, Enum):
    created = "created"
    running = "running"
    vulnerable = "vulnerable"
    awaiting_approval = "awaiting_approval"
    remediating = "remediating"
    verifying = "verifying"
    secured = "secured"
    validated = "validated"
    failed = "failed"
    rejected = "rejected"
    interrupted = "interrupted"
    aborted = "aborted"


class PolicyOutcome(str, Enum):
    permit = "PERMIT"
    permit_with_approval = "PERMIT_WITH_APPROVAL"
    block = "BLOCK"


class FindingAnalysis(WorkflowModel):
    classification: str = Field(min_length=1)
    severity: Severity
    confidence: ConfidenceLevel
    affected_component: TwinComponentName
    root_cause: str = Field(min_length=1)
    security_impact: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)


class RemediationPlan(WorkflowModel):
    remediation_id: str = Field(default_factory=lambda: f"REM-{uuid4().hex[:10].upper()}")
    title: str = Field(min_length=1)
    target_component: TwinComponentName
    action_type: str = Field(min_length=1)
    proposed_change: str = Field(min_length=1)
    risk: Severity = Severity.low
    expected_security_benefit: str = Field(min_length=1)
    possible_side_effects: list[str] = Field(default_factory=list)
    verification_test: str = Field(min_length=1)
    requires_human_approval: bool = True
    target_environment: str = "Digital Twin sandbox only"


class PolicyControlResult(WorkflowModel):
    control: str = Field(min_length=1)
    passed: bool
    evidence: str = Field(min_length=1)


class PolicyDecision(WorkflowModel):
    decision_id: str = Field(default_factory=lambda: f"POL-{uuid4().hex[:8].upper()}")
    action: str = Field(min_length=1)
    target: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    outcome: PolicyOutcome
    reason: str = Field(min_length=1)
    requires_human_approval: bool = False
    controls: list[PolicyControlResult] = Field(default_factory=list)
    decided_at: str = Field(default_factory=utc_now_iso)


class SimulationRun(WorkflowModel):
    run_id: str = Field(default_factory=lambda: f"RUN-{uuid4().hex[:10].upper()}")
    scenario_id: str = "SCN-001"
    scenario_name: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    status: RunStatus = RunStatus.created
    started_at: str = Field(default_factory=utc_now_iso)
    completed_at: str | None = None
    last_transition_at: str = Field(default_factory=utc_now_iso)
    failure_reason: str | None = None
    interrupted_at: str | None = None
    abort_reason: str | None = None
    model_name: str | None = None
    initial_twin_version: str = "1.0"
    final_twin_version: str | None = None
    initial_security_test: dict[str, Any] | None = None
    structured_finding: FindingAnalysis | None = None
    remediation_plan: RemediationPlan | None = None
    human_decision: str | None = None
    verification_test: dict[str, Any] | None = None
    result: str | None = None
    policy_decisions: list[PolicyDecision] = Field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
