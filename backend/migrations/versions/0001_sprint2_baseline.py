"""Sprint 2.1 schema baseline

Revision ID: 0001_sprint2_baseline
Revises: None
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_sprint2_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

appointment_status = sa.Enum(
    "PENDING", "CONFIRMED", "CHECKED_IN", "COMPLETED", "CANCELLED",
    "RESCHEDULED", "NO_SHOW", "EXPIRED", name="appointmentstatus"
)


def upgrade() -> None:
    op.create_table(
        "clinics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
    )
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("specialty", sa.String(length=120), nullable=True),
    )
    op.create_index("ix_doctors_clinic_id", "doctors", ["clinic_id"])
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
    )
    op.create_index("ix_services_clinic_id", "services", ["clinic_id"])
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=False),
        sa.Column("preferred_language", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_patients_clinic_id", "patients", ["clinic_id"])
    op.create_index("ix_patients_full_name", "patients", ["full_name"])
    op.create_index("ix_patients_phone", "patients", ["phone"])
    op.create_table(
        "doctor_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
    )
    op.create_index("ix_doctor_schedules_clinic_id", "doctor_schedules", ["clinic_id"])
    op.create_index("ix_doctor_schedules_doctor_id", "doctor_schedules", ["doctor_id"])
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("status", appointment_status, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_appointments_clinic_id", "appointments", ["clinic_id"])
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_service_id", "appointments", ["service_id"])
    op.create_index("ix_appointments_start_at", "appointments", ["start_at"])
    op.create_index("ix_appointments_end_at", "appointments", ["end_at"])
    op.create_index("ix_appointments_status", "appointments", ["status"])
    op.create_table(
        "appointment_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
    )
    op.create_index("ix_appointment_events_appointment_id", "appointment_events", ["appointment_id"])
    op.create_index("ix_appointment_events_event_type", "appointment_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_appointment_events_event_type", table_name="appointment_events")
    op.drop_index("ix_appointment_events_appointment_id", table_name="appointment_events")
    op.drop_table("appointment_events")
    for name in ["status", "end_at", "start_at", "service_id", "patient_id", "doctor_id", "clinic_id"]:
        op.drop_index(f"ix_appointments_{name}", table_name="appointments")
    op.drop_table("appointments")
    op.drop_index("ix_doctor_schedules_doctor_id", table_name="doctor_schedules")
    op.drop_index("ix_doctor_schedules_clinic_id", table_name="doctor_schedules")
    op.drop_table("doctor_schedules")
    op.drop_index("ix_patients_phone", table_name="patients")
    op.drop_index("ix_patients_full_name", table_name="patients")
    op.drop_index("ix_patients_clinic_id", table_name="patients")
    op.drop_table("patients")
    op.drop_index("ix_services_clinic_id", table_name="services")
    op.drop_table("services")
    op.drop_index("ix_doctors_clinic_id", table_name="doctors")
    op.drop_table("doctors")
    op.drop_table("clinics")
    appointment_status.drop(op.get_bind(), checkfirst=True)
