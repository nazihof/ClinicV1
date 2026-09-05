"""Sprint 3E waiting list and cancellation recovery.

Revision ID: 0003_waiting_list
Revises: 0002_risk_scores
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_waiting_list"
down_revision = "0002_risk_scores"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "waiting_list",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("preferred_day", sa.Date(), nullable=True),
        sa.Column("earliest_time", sa.Time(), nullable=True),
        sa.Column("latest_time", sa.Time(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ACTIVE"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_waiting_list_clinic_id", "waiting_list", ["clinic_id"])
    op.create_index("ix_waiting_list_patient_id", "waiting_list", ["patient_id"])
    op.create_index("ix_waiting_list_doctor_id", "waiting_list", ["doctor_id"])
    op.create_index("ix_waiting_list_service_id", "waiting_list", ["service_id"])
    op.create_index("ix_waiting_list_preferred_day", "waiting_list", ["preferred_day"])
    op.create_index("ix_waiting_list_status", "waiting_list", ["status"])


def downgrade():
    op.drop_index("ix_waiting_list_status", table_name="waiting_list")
    op.drop_index("ix_waiting_list_preferred_day", table_name="waiting_list")
    op.drop_index("ix_waiting_list_service_id", table_name="waiting_list")
    op.drop_index("ix_waiting_list_doctor_id", table_name="waiting_list")
    op.drop_index("ix_waiting_list_patient_id", table_name="waiting_list")
    op.drop_index("ix_waiting_list_clinic_id", table_name="waiting_list")
    op.drop_table("waiting_list")
