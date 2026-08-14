"""Add audit hash-chain metadata."""
from alembic import op
import sqlalchemy as sa
revision = "003_evidence_integrity"
down_revision = "002_run_lifecycle"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("audit_events", sa.Column("sequence_number", sa.Integer(), nullable=True))
    op.add_column("audit_events", sa.Column("previous_hash", sa.String(64), nullable=True))
    op.add_column("audit_events", sa.Column("event_hash", sa.String(64), nullable=True))
    op.add_column("audit_events", sa.Column("integrity_version", sa.String(20), nullable=True))
    op.create_index("ix_audit_events_run_sequence", "audit_events", ["run_id", "sequence_number"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_audit_events_run_sequence", table_name="audit_events")
    op.drop_column("audit_events", "integrity_version")
    op.drop_column("audit_events", "event_hash")
    op.drop_column("audit_events", "previous_hash")
    op.drop_column("audit_events", "sequence_number")
