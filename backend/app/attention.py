from datetime import date, datetime, time, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Appointment, AppointmentStatus
from .risk import calculate_appointment_risk


def _severity(rank: int) -> str:
    if rank >= 90:
        return "CRITICAL"
    if rank >= 70:
        return "HIGH"
    if rank >= 45:
        return "MEDIUM"
    return "LOW"


def build_attention_queue(
    db: Session,
    clinic_id: int,
    day: date,
    doctor_id: int | None = None,
    now: datetime | None = None,
):
    """Build one prioritized, actionable queue item per appointment for a selected day.

    The queue is deterministic and explainable. It does not use ML. Risk is delegated
    to the Sprint 3C risk engine and operational urgency is added here.
    """
    now = now or datetime.now()
    start = datetime.combine(day, time.min)
    end = start + timedelta(days=1)

    stmt = select(Appointment).where(
        Appointment.clinic_id == clinic_id,
        Appointment.start_at >= start,
        Appointment.start_at < end,
    )
    if doctor_id:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    appointments = db.scalars(stmt.order_by(Appointment.start_at)).all()

    items = []
    for a in appointments:
        signals = []
        rank = 0
        queue_type = None
        recommended_action = None
        quick_action = None
        risk = None

        # Finished states normally need no secretary action.
        if a.status in (AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW, AppointmentStatus.EXPIRED):
            continue

        # A stale appointment with an active status is operationally more urgent than risk.
        if a.status in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED, AppointmentStatus.CHECKED_IN) and a.start_at < now:
            queue_type = "OVERDUE_STATUS"
            rank = 100
            signals.append("Appointment time has passed but the workflow is still open")
            recommended_action = "Review the visit and mark it checked-in, completed, no-show or cancelled."

        if a.status == AppointmentStatus.CANCELLED:
            queue_type = "CANCELLED_SLOT"
            rank = max(rank, 78 if a.start_at >= now else 35)
            signals.append("A booked slot was cancelled")
            recommended_action = "Recover this empty slot from the waiting list."

        if a.status in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED):
            risk = calculate_appointment_risk(db, a, persist=True)
            if risk["level"] == "HIGH":
                if rank < 90:
                    queue_type = "HIGH_RISK"
                    recommended_action = "Contact the patient and reconfirm attendance."
                rank = max(rank, 80 + min(15, risk["score"] // 10))
                signals.append(f"High no-show risk ({risk['score']}/100)")
            elif risk["level"] == "MEDIUM":
                rank = max(rank, 48)
                signals.append(f"Medium no-show risk ({risk['score']}/100)")
                if queue_type is None:
                    queue_type = "RISK_REVIEW"
                    recommended_action = "Review the patient's risk factors before the appointment."

        if a.status == AppointmentStatus.PENDING:
            hours_to = (a.start_at - now).total_seconds() / 3600
            if hours_to >= 0 and hours_to <= 24:
                if rank < 96:
                    queue_type = "PENDING_CONFIRMATION"
                    recommended_action = "Confirm this appointment as soon as possible."
                rank = max(rank, 96)
                signals.append("Unconfirmed appointment is within 24 hours")
            elif hours_to > 24 and hours_to <= 48:
                if rank < 82:
                    queue_type = "PENDING_CONFIRMATION"
                    recommended_action = "Confirm this appointment today."
                rank = max(rank, 82)
                signals.append("Unconfirmed appointment is within 48 hours")
            elif hours_to > 48:
                if queue_type is None:
                    queue_type = "PENDING_CONFIRMATION"
                    recommended_action = "Confirm the appointment before the visit date."
                rank = max(rank, 58)
                signals.append("Appointment is still pending confirmation")
            if a.start_at >= now:
                quick_action = "confirm"

        # Confirmed low-risk future visits do not clutter the queue.
        if queue_type is None:
            continue

        items.append({
            "type": queue_type,
            "severity": _severity(rank),
            "priority_score": rank,
            "appointment_id": a.id,
            "patient_id": a.patient_id,
            "patient_name": a.patient.full_name,
            "patient_phone": a.patient.phone,
            "doctor_name": a.doctor.name,
            "service_name": a.service.name,
            "start_at": a.start_at,
            "status": a.status.value,
            "risk_score": risk["score"] if risk else None,
            "risk_level": risk["level"] if risk else None,
            "signals": signals,
            "recommended_action": recommended_action,
            "quick_action": quick_action,
        })

    items.sort(key=lambda x: (-x["priority_score"], x["start_at"], x["patient_name"]))
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for item in items:
        counts[item["severity"]] += 1
    return {"total": len(items), "counts": counts, "items": items}
