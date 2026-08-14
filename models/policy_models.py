from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class PolicyEffect(str, Enum):
    permit = "permit"
    require_approval = "require_approval"
    block = "block"


class RuleEvaluationStatus(str, Enum):
    pass_ = "PASS"
    pending = "PENDING"
    fail = "FAIL"


class PolicyRule(BaseModel):
    model_config = ConfigDict(validate_assignment=True, str_strip_whitespace=True)
    rule_id: str
    name: str
    category: str
    description: str
    effect: PolicyEffect
    enabled: bool = True
    priority: int = Field(default=100, ge=0)


class PolicyRuleResult(BaseModel):
    rule_id: str
    status: RuleEvaluationStatus
    passed: bool
    evidence: str
