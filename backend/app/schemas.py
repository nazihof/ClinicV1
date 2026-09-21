from datetime import datetime, time, date
from pydantic import BaseModel, ConfigDict
from .models import AppointmentStatus

class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WhatsAppSendRequest(BaseModel):
    phone_number_id: str
    recipient: str
    message: str


class WhatsAppConversationOut(BaseModel):
    id: int
    clinic_id: int
    wa_contact_id: str
    phone_number_id: str
    contact_name: str | None = None
    status: str
    last_message_at: datetime | None = None


class WhatsAppMessageOut(BaseModel):
    id: int
    conversation_id: int
    provider_message_id: str | None = None
    direction: str
    message_type: str
    body: str | None = None
    status: str
    provider_timestamp: datetime | None = None
    created_at: datetime

class WhatsAppTemplateSendRequest(BaseModel):
    phone_number_id: str
    recipient: str
    template_name: str
    language_code: str = "en_US"

class ClinicCreate(BaseModel):
    name: str
    timezone: str = "Asia/Beirut"
class ClinicOut(ORM):
    id: int; name: str; timezone: str

class DoctorCreate(BaseModel):
    clinic_id: int; name: str; specialty: str | None = None
class DoctorOut(ORM):
    id: int; clinic_id: int; name: str; specialty: str | None = None

class ServiceCreate(BaseModel):
    clinic_id: int; name: str; duration_minutes: int;is_active: bool = True; price: float | None = None
class ServiceOut(ORM):
    id: int; clinic_id: int; name: str; duration_minutes: int;is_active:bool; price: float | None = None

class PatientCreate(BaseModel):
    clinic_id: int; full_name: str; phone: str; preferred_language: str = "ar"; notes: str | None = None
class PatientOut(ORM):
    id: int; clinic_id: int; full_name: str; phone: str; preferred_language: str; notes: str | None = None

class ScheduleCreate(BaseModel):
    clinic_id: int; weekday: int; start_time: time; end_time: time
class ScheduleOut(ORM):
    id: int; clinic_id: int; doctor_id: int; weekday: int; start_time: time; end_time: time

class AppointmentCreate(BaseModel):
    clinic_id: int; doctor_id: int; patient_id: int; service_id: int; start_at: datetime
class AppointmentReschedule(BaseModel):
    start_at: datetime

class AppointmentOut(ORM):
    id: int; clinic_id: int; doctor_id: int; patient_id: int; service_id: int
    start_at: datetime; end_at: datetime; status: AppointmentStatus

class AppointmentView(AppointmentOut):
    patient_name: str
    patient_phone: str
    doctor_name: str
    service_name: str
    duration_minutes: int
    price: float | None = None

class EventOut(ORM):
    id: int; appointment_id: int; event_type: str; created_at: datetime; details: str | None = None

class AvailabilitySlot(BaseModel):
    start_at: datetime
    end_at: datetime

class ClinicUpdate(BaseModel):
    name: str
    timezone: str = "Asia/Beirut"

class DoctorUpdate(BaseModel):
    name: str
    specialty: str | None = None

class ServiceUpdate(BaseModel):
    name: str
    duration_minutes: int
    price: float | None = None

class ScheduleUpdate(BaseModel):
    weekday: int
    start_time: time
    end_time: time

class RiskReason(BaseModel):
    code: str
    points: int
    detail: str

class RiskOut(BaseModel):
    appointment_id: int
    patient_id: int
    score: int
    level: str
    reasons: list[RiskReason]
    calculated_at: datetime

class PatientHistoryOut(BaseModel):
    patient_id: int
    total_appointments: int
    completed: int
    cancelled: int
    no_show: int
    confirmed: int
    pending: int
    no_show_rate_percent: float
    last_completed_visit: datetime | None = None


class AttentionItemOut(BaseModel):
    type: str
    severity: str
    priority_score: int
    appointment_id: int
    patient_id: int
    patient_name: str
    patient_phone: str
    doctor_name: str
    service_name: str
    start_at: datetime
    status: str
    risk_score: int | None = None
    risk_level: str | None = None
    signals: list[str]
    recommended_action: str
    quick_action: str | None = None

class AttentionQueueOut(BaseModel):
    total: int
    counts: dict[str, int]
    items: list[AttentionItemOut]


class WaitingListCreate(BaseModel):
    clinic_id: int
    patient_id: int
    doctor_id: int
    service_id: int
    preferred_day: date | None = None
    earliest_time: time | None = None
    latest_time: time | None = None
    priority: int = 0
    notes: str | None = None

class WaitingListOut(ORM):
    id: int
    clinic_id: int
    patient_id: int
    doctor_id: int
    service_id: int
    preferred_day: date | None = None
    earliest_time: time | None = None
    latest_time: time | None = None
    priority: int
    status: str
    notes: str | None = None
    created_at: datetime

class WaitingListView(WaitingListOut):
    patient_name: str
    patient_phone: str
    doctor_name: str
    service_name: str

class RecoveryCandidateOut(BaseModel):
    waiting_list_id: int
    patient_id: int
    patient_name: str
    patient_phone: str
    priority_score: int
    reasons: list[str]
    preferred_day: date | None = None
    earliest_time: time | None = None
    latest_time: time | None = None

class RecoveryResultOut(BaseModel):
    cancelled_appointment_id: int
    new_appointment_id: int
    waiting_list_id: int
    patient_id: int
    start_at: datetime
    status: str

class SetupOwner(BaseModel):
    clinic_id: int | None = None
    clinic_name: str | None = None
    timezone: str = "Asia/Beirut"
    full_name: str
    email: str
    password: str
class LoginIn(BaseModel):
    email: str
    password: str
class UserOut(BaseModel):
    id:int
    clinic_id:int
    doctor_id:int | None = None
    email:str
    full_name:str
    role:str
    is_active:bool

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "SECRETARY"
    doctor_id: int | None = None

class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    doctor_id: int | None = None
    is_active: bool | None = None
    password: str | None = None
class TokenOut(BaseModel):
    access_token:str
    token_type:str="bearer"
    user:UserOut


class AuditLogOut(ORM):
    id: int
    clinic_id: int | None = None
    user_id: int | None = None
    action: str
    method: str
    path: str
    status_code: int
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime
