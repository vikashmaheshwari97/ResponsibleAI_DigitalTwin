"""Add explicit run lifecycle metadata."""
from alembic import op
import sqlalchemy as sa
revision = "002_run_lifecycle"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("simulation_runs", sa.Column("last_transition_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("simulation_runs", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.add_column("simulation_runs", sa.Column("interrupted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("simulation_runs", sa.Column("abort_reason", sa.Text(), nullable=True))
    op.execute("UPDATE simulation_runs SET last_transition_at = COALESCE(completed_at, started_at) WHERE last_transition_at IS NULL")

def downgrade() -> None:
    op.drop_column("simulation_runs", "abort_reason")
    op.drop_column("simulation_runs", "interrupted_at")
    op.drop_column("simulation_runs", "failure_reason")
    op.drop_column("simulation_runs", "last_transition_at")
