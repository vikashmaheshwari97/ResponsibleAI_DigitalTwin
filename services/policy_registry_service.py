from __future__ import annotations

from sqlalchemy import select

from models.database_models import PolicyRuleRecord, PolicyRuleResultRecord
from models.policy_models import (
    PolicyEffect,
    PolicyRule,
    PolicyRuleResult,
    RuleEvaluationStatus,
)
from services.database_service import get_database_session


DEFAULT_RULES = [
    PolicyRule(
        rule_id="POL-SBX-001",
        name="Sandbox-only execution",
        category="Environment",
        description=(
            "Security validation and remediation must remain inside the approved "
            "Digital Twin sandbox."
        ),
        effect=PolicyEffect.block,
        priority=10,
    ),
    PolicyRule(
        rule_id="POL-DATA-001",
        name="Synthetic data only",
        category="Data",
        description="The PoC may use only synthetic users, messages, and test evidence.",
        effect=PolicyEffect.block,
        priority=20,
    ),
    PolicyRule(
        rule_id="POL-NET-001",
        name="External targets prohibited",
        category="Network",
        description="The workflow may not target systems outside the local approved sandbox.",
        effect=PolicyEffect.block,
        priority=30,
    ),
    PolicyRule(
        rule_id="POL-DB-001",
        name="Persistent evidence store required",
        category="Audit",
        description="PostgreSQL must be available before governed workflow actions are permitted.",
        effect=PolicyEffect.block,
        priority=40,
    ),
    PolicyRule(
        rule_id="POL-SCN-001",
        name="Approved scenario registry",
        category="Scenario Governance",
        description="Only predefined controlled scenarios in the local scenario registry may execute.",
        effect=PolicyEffect.block,
        priority=45,
    ),
    PolicyRule(
        rule_id="POL-RBAC-001",
        name="Role-authorized execution",
        category="Access Control",
        description="Only admin/operator roles may execute or approve validation remediation workflows.",
        effect=PolicyEffect.block,
        priority=47,
    ),
    PolicyRule(
        rule_id="POL-HUM-001",
        name="Human approval for remediation",
        category="Human Oversight",
        description="Security-changing remediation requires explicit human approval before execution.",
        effect=PolicyEffect.require_approval,
        priority=50,
    ),
    PolicyRule(
        rule_id="POL-AUD-001",
        name="Auditable privileged actions",
        category="Audit",
        description="Agent, policy, sandbox, verification, and human actions must be recorded.",
        effect=PolicyEffect.block,
        priority=60,
    ),
    PolicyRule(
        rule_id="POL-VER-001",
        name="Verification required",
        category="Verification",
        description="A remediation cannot be marked secured without a successful controlled verification test.",
        effect=PolicyEffect.block,
        priority=70,
    ),
]


def seed_policy_rules() -> None:
    with get_database_session() as db:
        for rule in DEFAULT_RULES:
            existing = db.get(PolicyRuleRecord, rule.rule_id)
            if existing is None:
                db.add(
                    PolicyRuleRecord(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        category=rule.category,
                        description=rule.description,
                        effect=rule.effect.value,
                        enabled=rule.enabled,
                        priority=rule.priority,
                    )
                )
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
        stmt = (
            select(PolicyRuleRecord)
            .where(PolicyRuleRecord.enabled.is_(True))
            .order_by(PolicyRuleRecord.priority.asc())
        )
        return list(db.scalars(stmt).all())


def save_rule_results(
    decision_id: str,
    run_id: str,
    results: list[PolicyRuleResult],
) -> None:
    with get_database_session() as db:
        for result in results:
            stmt = select(PolicyRuleResultRecord).where(
                PolicyRuleResultRecord.decision_id == decision_id,
                PolicyRuleResultRecord.rule_id == result.rule_id,
            )
            record = db.scalars(stmt).first()
            if record is None:
                db.add(
                    PolicyRuleResultRecord(
                        decision_id=decision_id,
                        run_id=run_id,
                        rule_id=result.rule_id,
                        status=result.status.value,
                        passed=result.passed,
                        evidence=result.evidence,
                    )
                )
            else:
                record.status = result.status.value
                record.passed = result.passed
                record.evidence = result.evidence
        db.commit()


def _result(rule_id: str, passed: bool, evidence: str) -> PolicyRuleResult:
    return PolicyRuleResult(
        rule_id=rule_id,
        status=RuleEvaluationStatus.pass_ if passed else RuleEvaluationStatus.fail,
        passed=passed,
        evidence=evidence,
    )


def build_rule_results(
    *,
    environment_ok: bool,
    target_ok: bool,
    synthetic_data: bool,
    database_ok: bool,
    audit_ok: bool,
    scenario_approved: bool,
    actor_authorized: bool,
    requires_human_approval: bool,
    human_approved: bool,
    verification_ok: bool | None = None,
) -> list[PolicyRuleResult]:
    results = [
        _result(
            "POL-SBX-001",
            environment_ok and target_ok,
            "Approved Digital Twin sandbox and target."
            if environment_ok and target_ok
            else "Action leaves the approved sandbox/target boundary.",
        ),
        _result(
            "POL-DATA-001",
            synthetic_data,
            "Scenario uses synthetic PoC records only."
            if synthetic_data
            else "Non-synthetic data detected.",
        ),
        _result(
            "POL-NET-001",
            True,
            "Workflow restricted to the local SecureMessenger sandbox.",
        ),
        _result(
            "POL-DB-001",
            database_ok,
            "PostgreSQL evidence store connected."
            if database_ok
            else "Persistent evidence store unavailable.",
        ),
        _result(
            "POL-SCN-001",
            scenario_approved,
            "Scenario is present in the approved local registry."
            if scenario_approved
            else "Scenario is not present in the approved registry.",
        ),
        _result(
            "POL-RBAC-001",
            actor_authorized,
            "Current role is authorized for this governed action."
            if actor_authorized
            else "Current role is not authorized for this governed action.",
        ),
        _result(
            "POL-AUD-001",
            audit_ok,
            "Audit logging enabled." if audit_ok else "Audit logging unavailable.",
        ),
    ]

    if requires_human_approval:
        results.append(
            PolicyRuleResult(
                rule_id="POL-HUM-001",
                status=(
                    RuleEvaluationStatus.pass_
                    if human_approved
                    else RuleEvaluationStatus.pending
                ),
                passed=human_approved,
                evidence=(
                    "Human approval recorded."
                    if human_approved
                    else "Human approval required before execution."
                ),
            )
        )

    if verification_ok is not None:
        results.append(
            _result(
                "POL-VER-001",
                verification_ok,
                "Controlled verification passed."
                if verification_ok
                else "Controlled verification has not passed.",
            )
        )

    return results
