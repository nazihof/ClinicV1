from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
from .models import Appointment, AppointmentStatus, DoctorSchedule, Service

ACTIVE = [AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED, AppointmentStatus.CHECKED_IN]

def validate_entities(db: Session, clinic_id: int, doctor_id: int, patient_id: int, service_id: int):
    from .models import Doctor, Patient, Service
    doctor = db.get(Doctor, doctor_id)
    patient = db.get(Patient, patient_id)
    service = db.get(Service, service_id)
    if not doctor or doctor.clinic_id != clinic_id: raise HTTPException(404, "Doctor not found in clinic")
    if not patient or patient.clinic_id != clinic_id: raise HTTPException(404, "Patient not found in clinic")
    if not service or service.clinic_id != clinic_id: raise HTTPException(404, "Service not found in clinic")
    return doctor, patient, service

def ensure_in_schedule(db: Session, clinic_id: int, doctor_id: int, start_at: datetime, end_at: datetime):
    weekday = start_at.weekday()
    schedules = db.scalars(select(DoctorSchedule).where(
        DoctorSchedule.clinic_id == clinic_id,
        DoctorSchedule.doctor_id == doctor_id,
        DoctorSchedule.weekday == weekday
    )).all()
    if not any(start_at.time() >= s.start_time and end_at.time() <= s.end_time for s in schedules):
        raise HTTPException(400, "Requested time is outside doctor working schedule")

def ensure_no_overlap(db: Session, clinic_id: int, doctor_id: int, start_at: datetime, end_at: datetime, exclude_id: int | None = None):
    q = select(Appointment).where(
        Appointment.clinic_id == clinic_id,
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_(ACTIVE),
        Appointment.start_at < end_at,
        Appointment.end_at > start_at,
    )
    if exclude_id is not None:
        q = q.where(Appointment.id != exclude_id)
    if db.scalar(q):
        raise HTTPException(409, "Doctor is already booked during this time")

def calculate_end(start_at: datetime, duration_minutes: int):
    return start_at + timedelta(minutes=duration_minutes)
