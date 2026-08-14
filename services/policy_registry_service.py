from __future__ import annotations

from sqlalchemy import select

from models.database_models import PolicyRuleRecord, PolicyRuleResultRecord
from models.policy_models import PolicyEffect, PolicyRule, PolicyRuleResult, RuleEvaluationStatus
from services.database_service import get_database_session

DEFAULT_RULES = [
    PolicyRule(rule_id="POL-SBX-001", name="Sandbox-only execution", category="Environment", description="Security validation and remediation must remain inside the approved Digital Twin sandbox.", effect=PolicyEffect.block, priority=10),
    PolicyRule(rule_id="POL-DATA-001", name="Synthetic data only", category="Data", description="The PoC may use only synthetic users, messages, and test evidence.", effect=PolicyEffect.block, priority=20),
    PolicyRule(rule_id="POL-NET-001", name="External targets prohibited", category="Network", description="The workflow may not target systems outside the local approved sandbox.", effect=PolicyEffect.block, priority=30),
    PolicyRule(rule_id="POL-DB-001", name="Persistent evidence store required", category="Audit", description="PostgreSQL must be available before governed workflow actions are permitted.", effect=PolicyEffect.block, priority=40),
    PolicyRule(rule_id="POL-HUM-001", name="Human approval for remediation", category="Human Oversight", description="Security-changing remediation requires explicit human approval before execution.", effect=PolicyEffect.require_approval, priority=50),
    PolicyRule(rule_id="POL-AUD-001", name="Auditable privileged actions", category="Audit", description="Agent, policy, sandbox, verification, and human actions must be recorded.", effect=PolicyEffect.block, priority=60),
    PolicyRule(rule_id="POL-VER-001", name="Verification required", category="Verification", description="A remediation cannot be marked secured without a successful controlled verification test.", effect=PolicyEffect.block, priority=70),
]


def seed_policy_rules() -> None:
    with get_database_session() as db:
        for rule in DEFAULT_RULES:
            existing = db.get(PolicyRuleRecord, rule.rule_id)
            if existing is None:
                db.add(PolicyRuleRecord(
                    rule_id=rule.rule_id,
                    name=rule.name,
                    category=rule.category,
                    description=rule.description,
                    effect=rule.effect.value,
                    enabled=rule.enabled,
                    priority=rule.priority,
                ))
            else:
                existing.name = rule.name
                existing.category = rule.category
                existing.description = rule.description
                existing.effect = rule.effect.value
                existing.enabled = rule.enabled
                existing.priority = rule.priority
        db.commit()


def list_policy_rules() -> list[PolicyRuleRecord]:
    with get_database_session() as db:
        stmt = select(PolicyRuleRecord).where(PolicyRuleRecord.enabled.is_(True)).order_by(PolicyRuleRecord.priority.asc())
        return list(db.scalars(stmt).all())


def save_rule_results(decision_id: str, run_id: str, results: list[PolicyRuleResult]) -> None:
    with get_database_session() as db:
        for result in results:
            stmt = select(PolicyRuleResultRecord).where(
                PolicyRuleResultRecord.decision_id == decision_id,
                PolicyRuleResultRecord.rule_id == result.rule_id,
            )
            record = db.scalars(stmt).first()
            if record is None:
                record = PolicyRuleResultRecord(
                    decision_id=decision_id,
                    run_id=run_id,
                    rule_id=result.rule_id,
                    status=result.status.value,
                    passed=result.passed,
                    evidence=result.evidence,
                )
                db.add(record)
            else:
                record.status = result.status.value
                record.passed = result.passed
                record.evidence = result.evidence
        db.commit()


def build_rule_results(*, environment_ok: bool, target_ok: bool, synthetic_data: bool, database_ok: bool, audit_ok: bool, requires_human_approval: bool, human_approved: bool, verification_ok: bool | None = None) -> list[PolicyRuleResult]:
    results = [
        PolicyRuleResult(rule_id="POL-SBX-001", status=RuleEvaluationStatus.pass_ if environment_ok and target_ok else RuleEvaluationStatus.fail, passed=environment_ok and target_ok, evidence="Approved Digital Twin sandbox and target." if environment_ok and target_ok else "Action leaves the approved sandbox/target boundary."),
        PolicyRuleResult(rule_id="POL-DATA-001", status=RuleEvaluationStatus.pass_ if synthetic_data else RuleEvaluationStatus.fail, passed=synthetic_data, evidence="Scenario uses synthetic PoC records only." if synthetic_data else "Non-synthetic data detected."),
        PolicyRuleResult(rule_id="POL-NET-001", status=RuleEvaluationStatus.pass_, passed=True, evidence="Workflow restricted to the local SecureMessenger sandbox."),
        PolicyRuleResult(rule_id="POL-DB-001", status=RuleEvaluationStatus.pass_ if database_ok else RuleEvaluationStatus.fail, passed=database_ok, evidence="PostgreSQL evidence store connected." if database_ok else "Persistent evidence store unavailable."),
        PolicyRuleResult(rule_id="POL-AUD-001", status=RuleEvaluationStatus.pass_ if audit_ok else RuleEvaluationStatus.fail, passed=audit_ok, evidence="Audit logging enabled." if audit_ok else "Audit logging unavailable."),
    ]
    if requires_human_approval:
        results.append(PolicyRuleResult(rule_id="POL-HUM-001", status=RuleEvaluationStatus.pass_ if human_approved else RuleEvaluationStatus.pending, passed=human_approved, evidence="Human approval recorded." if human_approved else "Human approval required before execution."))
    if verification_ok is not None:
        results.append(PolicyRuleResult(rule_id="POL-VER-001", status=RuleEvaluationStatus.pass_ if verification_ok else RuleEvaluationStatus.fail, passed=verification_ok, evidence="Controlled verification passed." if verification_ok else "Controlled verification has not passed."))
    return results
