"""Add persistent Digital Twin snapshots."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "005_twin_snapshots"
down_revision = "004_policy_registry"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "twin_snapshots",
        sa.Column("snapshot_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("twin_version", sa.String(50), nullable=False),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("trigger", sa.String(255), nullable=False),
        sa.Column("state_json", postgresql.JSONB(), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_twin_snapshots_run_id", "twin_snapshots", ["run_id"])

def downgrade() -> None:
    op.drop_index("ix_twin_snapshots_run_id", table_name="twin_snapshots")
    op.drop_table("twin_snapshots")
