import json
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Appointment, AppointmentEvent, AppointmentStatus, RiskScore

RISK_LOW_MAX = 29
RISK_MEDIUM_MAX = 59
LONG_LEAD_DAYS = 7
LATE_CANCEL_HOURS = 24


def risk_level(score: int) -> str:
    if score <= RISK_LOW_MAX:
        return "LOW"
    if score <= RISK_MEDIUM_MAX:
        return "MEDIUM"
    return "HIGH"


def _events_for(db: Session, appointment_id: int):
    return db.scalars(
        select(AppointmentEvent)
        .where(AppointmentEvent.appointment_id == appointment_id)
        .order_by(AppointmentEvent.created_at)
    ).all()


def calculate_appointment_risk(db: Session, appointment: Appointment, persist: bool = True):
    """Explainable rule-based no-show risk. No ML claims are made."""
    prior = db.scalars(
        select(Appointment)
        .where(
            Appointment.patient_id == appointment.patient_id,
            Appointment.id != appointment.id,
            Appointment.start_at < appointment.start_at,
        )
        .order_by(Appointment.start_at.desc())
    ).all()

    reasons = []
    score = 0

    # Any previous no-show is a strong signal. Keep the rule explainable and capped.
    prior_no_shows = sum(1 for a in prior if a.status == AppointmentStatus.NO_SHOW)
    if prior_no_shows:
        points = min(50, prior_no_shows * 25)
        score += points
        reasons.append({"code": "PREVIOUS_NO_SHOW", "points": points, "detail": f"{prior_no_shows} previous no-show(s)"})

    # A cancellation counts as late only when its cancellation event is within 24h of that slot.
    late_cancels = 0
    for old in prior:
        if old.status != AppointmentStatus.CANCELLED:
            continue
        cancelled = next((e for e in reversed(_events_for(db, old.id)) if e.event_type == "CANCELLED"), None)
        if cancelled and cancelled.created_at >= old.start_at - timedelta(hours=LATE_CANCEL_HOURS):
            late_cancels += 1
    if late_cancels:
        points = min(30, late_cancels * 15)
        score += points
        reasons.append({"code": "LATE_CANCELLATION", "points": points, "detail": f"{late_cancels} late cancellation(s)"})

    if appointment.status == AppointmentStatus.PENDING:
        score += 20
        reasons.append({"code": "NOT_CONFIRMED", "points": 20, "detail": "Appointment is still pending confirmation"})

    completed_before = sum(1 for a in prior if a.status == AppointmentStatus.COMPLETED)
    if completed_before == 0:
        score += 10
        reasons.append({"code": "NEW_PATIENT", "points": 10, "detail": "No completed visit history yet"})

    if appointment.created_at and appointment.start_at - appointment.created_at >= timedelta(days=LONG_LEAD_DAYS):
        score += 10
        reasons.append({"code": "LONG_LEAD_TIME", "points": 10, "detail": f"Booked at least {LONG_LEAD_DAYS} days in advance"})

    # Reserved for Sprint 4 reminders. If REMINDER_SENT exists and there is no later CONFIRMED event,
    # the same engine already knows how to score an ignored reminder.
    events = _events_for(db, appointment.id)
    reminders = [e for e in events if e.event_type == "REMINDER_SENT"]
    if reminders:
        latest_reminder = reminders[-1]
        confirmed_after = any(e.event_type == "CONFIRMED" and e.created_at > latest_reminder.created_at for e in events)
        if not confirmed_after and appointment.status == AppointmentStatus.PENDING:
            score += 15
            reasons.append({"code": "IGNORED_REMINDER", "points": 15, "detail": "Reminder sent without a later confirmation"})

    score = min(100, score)
    result = {"score": score, "level": risk_level(score), "reasons": reasons, "calculated_at": datetime.utcnow()}

    if persist:
        row = db.scalar(select(RiskScore).where(RiskScore.appointment_id == appointment.id))
        if row is None:
            row = RiskScore(clinic_id=appointment.clinic_id, patient_id=appointment.patient_id, appointment_id=appointment.id)
            db.add(row)
        row.score = score
        row.level = result["level"]
        row.reasons_json = json.dumps(reasons)
        row.calculated_at = result["calculated_at"]
        db.flush()
    return result


def patient_history(db: Session, patient_id: int):
    rows = db.scalars(
        select(Appointment).where(Appointment.patient_id == patient_id).order_by(Appointment.start_at.desc())
    ).all()
    counts = {s.value: 0 for s in AppointmentStatus}
    for a in rows:
        counts[a.status.value] += 1
    completed = counts[AppointmentStatus.COMPLETED.value]
    no_show = counts[AppointmentStatus.NO_SHOW.value]
    cancelled = counts[AppointmentStatus.CANCELLED.value]
    attended_base = completed + no_show
    no_show_rate = round((no_show / attended_base) * 100, 1) if attended_base else 0.0
    last_completed = next((a.start_at for a in rows if a.status == AppointmentStatus.COMPLETED), None)
    return {
        "patient_id": patient_id,
        "total_appointments": len(rows),
        "completed": completed,
        "cancelled": cancelled,
        "no_show": no_show,
        "confirmed": counts[AppointmentStatus.CONFIRMED.value],
        "pending": counts[AppointmentStatus.PENDING.value],
        "no_show_rate_percent": no_show_rate,
        "last_completed_visit": last_completed,
    }
