"""Initial PostgreSQL evidence schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "simulation_runs",
        sa.Column("run_id", sa.String(64), primary_key=True),
        sa.Column("scenario_id", sa.String(64), nullable=False),
        sa.Column("scenario_name", sa.String(255), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=True),
        sa.Column("initial_twin_version", sa.String(50), nullable=False),
        sa.Column("final_twin_version", sa.String(50), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "security_tests",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("scenario", sa.String(255), nullable=False),
        sa.Column("requesting_user", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=False),
        sa.Column("expected_owner", sa.String(100), nullable=True),
        sa.Column("observed_owner", sa.String(100), nullable=True),
        sa.Column("expected_status", sa.Integer(), nullable=False),
        sa.Column("observed_status", sa.Integer(), nullable=False),
        sa.Column("access_granted", sa.Boolean(), nullable=False),
        sa.Column("vulnerability_detected", sa.Boolean(), nullable=False),
        sa.Column("response_json", postgresql.JSONB(), nullable=False),
        sa.Column("result", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_security_tests_run_id", "security_tests", ["run_id"])
    op.create_table(
        "findings",
        sa.Column("finding_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("classification", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("confidence_level", sa.String(50), nullable=False),
        sa.Column("affected_component", sa.String(255), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("security_impact", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_findings_run_id", "findings", ["run_id"])
    op.create_table(
        "remediations",
        sa.Column("remediation_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("target_component", sa.String(255), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("proposed_change", sa.Text(), nullable=False),
        sa.Column("risk", sa.String(50), nullable=False),
        sa.Column("expected_security_benefit", sa.Text(), nullable=False),
        sa.Column("possible_side_effects", postgresql.JSONB(), nullable=False),
        sa.Column("verification_test", sa.Text(), nullable=False),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False),
        sa.Column("target_environment", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_remediations_run_id", "remediations", ["run_id"])
    op.create_table(
        "human_decisions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("remediation_id", sa.String(64), nullable=True),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_human_decisions_run_id", "human_decisions", ["run_id"])
    op.create_table(
        "policy_decisions",
        sa.Column("decision_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("environment", sa.String(255), nullable=False),
        sa.Column("outcome", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False),
        sa.Column("controls_json", postgresql.JSONB(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_policy_decisions_run_id", "policy_decisions", ["run_id"])
    op.create_table(
        "agent_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("agent", sa.String(255), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_events_run_id", "agent_events", ["run_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=True),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_audit_events_run_id", "audit_events", ["run_id"])

def downgrade() -> None:
    op.drop_index("ix_audit_events_run_id", table_name="audit_events"); op.drop_table("audit_events")
    op.drop_index("ix_agent_events_run_id", table_name="agent_events"); op.drop_table("agent_events")
    op.drop_index("ix_policy_decisions_run_id", table_name="policy_decisions"); op.drop_table("policy_decisions")
    op.drop_index("ix_human_decisions_run_id", table_name="human_decisions"); op.drop_table("human_decisions")
    op.drop_index("ix_remediations_run_id", table_name="remediations"); op.drop_table("remediations")
    op.drop_index("ix_findings_run_id", table_name="findings"); op.drop_table("findings")
    op.drop_index("ix_security_tests_run_id", table_name="security_tests"); op.drop_table("security_tests")
    op.drop_table("simulation_runs")
