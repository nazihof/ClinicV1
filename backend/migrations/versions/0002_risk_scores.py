"""Sprint 3B/3C patient history + explainable risk storage.

Revision ID: 0002_risk_scores
Revises: 0001_sprint2_baseline
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_risk_scores"
down_revision = "0001_sprint2_baseline"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "risk_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.String(length=16), nullable=False, server_default="LOW"),
        sa.Column("reasons_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("calculated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("appointment_id", name="uq_risk_scores_appointment_id"),
    )
    op.create_index("ix_risk_scores_clinic_id", "risk_scores", ["clinic_id"])
    op.create_index("ix_risk_scores_patient_id", "risk_scores", ["patient_id"])
    op.create_index("ix_risk_scores_appointment_id", "risk_scores", ["appointment_id"])
    op.create_index("ix_risk_scores_level", "risk_scores", ["level"])


def downgrade():
    op.drop_index("ix_risk_scores_level", table_name="risk_scores")
    op.drop_index("ix_risk_scores_appointment_id", table_name="risk_scores")
    op.drop_index("ix_risk_scores_patient_id", table_name="risk_scores")
    op.drop_index("ix_risk_scores_clinic_id", table_name="risk_scores")
    op.drop_table("risk_scores")
