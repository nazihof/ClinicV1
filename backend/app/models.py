import enum
from datetime import datetime, date, time
from sqlalchemy import String, Integer, ForeignKey, DateTime, Date,Boolean, Time, Numeric, Enum,text, Text,func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    SECRETARY = "SECRETARY"
    DOCTOR = "DOCTOR"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), index=True)
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.id"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.SECRETARY, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    method: Mapped[str] = mapped_column(String(12))
    path: Mapped[str] = mapped_column(String(255))
    status_code: Mapped[int] = mapped_column(Integer, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class AppointmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    NO_SHOW = "NO_SHOW"
    EXPIRED = "EXPIRED"

class Clinic(Base):
    __tablename__ = "clinics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Beirut")

class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str | None] = mapped_column(String(120), nullable=True)

class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[float | None] = mapped_column(Numeric(10,2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean,nullable=False,default=True,server_default=text("true"))

class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    phone: Mapped[str] = mapped_column(String(40), index=True)
    preferred_language: Mapped[str] = mapped_column(String(16), default="ar")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    doctor = relationship("Doctor")
    patient = relationship("Patient")
    service = relationship("Service")

class AppointmentEvent(Base):
    __tablename__ = "appointment_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)


class RiskScore(Base):
    __tablename__ = "risk_scores"
    __table_args__ = (UniqueConstraint("appointment_id", name="uq_risk_scores_appointment_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String(16), default="LOW", index=True)
    reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WaitingListEntry(Base):
    __tablename__ = "waiting_list"
    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    preferred_day: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    earliest_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    latest_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    patient = relationship("Patient")
    doctor = relationship("Doctor")
    service = relationship("Service")


class WhatsAppChannel(Base):
    __tablename__ = "whatsapp_channels"

    id: Mapped[int] = mapped_column(primary_key=True)

    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Meta identifiers
    waba_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    phone_number_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    display_phone_number: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # We will encrypt/decrypt this in a later 4A step.
    access_token_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)

    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id: Mapped[int | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    whatsapp_channel_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # WhatsApp user's identifier / phone
    wa_contact_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    contact_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # OPEN / HUMAN / CLOSED
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        server_default="OPEN",
    )

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "whatsapp_channel_id",
            "wa_contact_id",
            name="uq_conversation_channel_contact",
        ),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Meta WhatsApp message ID.
    # Unique prevents duplicated webhook delivery from creating duplicates.
    provider_message_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
        index=True,
    )

    # INBOUND / OUTBOUND
    direction: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    # text / image / document / audio / etc.
    message_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="text",
        server_default="text",
    )

    body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # RECEIVED / SENT / DELIVERED / READ / FAILED
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    provider_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
