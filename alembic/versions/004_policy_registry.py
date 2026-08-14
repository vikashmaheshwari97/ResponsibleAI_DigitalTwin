"""Add persistent policy registry."""
from alembic import op
import sqlalchemy as sa
revision = "004_policy_registry"
down_revision = "003_evidence_integrity"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "policy_rules",
        sa.Column("rule_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("effect", sa.String(50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "policy_rule_results",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("decision_id", sa.String(64), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("rule_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["policy_decisions.decision_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["policy_rules.rule_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("decision_id", "rule_id", name="uq_policy_rule_result_decision_rule"),
    )
    op.create_index("ix_policy_rule_results_decision_id", "policy_rule_results", ["decision_id"])
    op.create_index("ix_policy_rule_results_run_id", "policy_rule_results", ["run_id"])
    op.create_index("ix_policy_rule_results_rule_id", "policy_rule_results", ["rule_id"])

def downgrade() -> None:
    op.drop_index("ix_policy_rule_results_rule_id", table_name="policy_rule_results")
    op.drop_index("ix_policy_rule_results_run_id", table_name="policy_rule_results")
    op.drop_index("ix_policy_rule_results_decision_id", table_name="policy_rule_results")
    op.drop_table("policy_rule_results")
    op.drop_table("policy_rules")
