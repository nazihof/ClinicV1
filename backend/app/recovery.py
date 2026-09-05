from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Appointment, AppointmentStatus, WaitingListEntry
from .booking import ACTIVE


def recovery_candidates(db: Session, cancelled: Appointment):
    if cancelled.status != AppointmentStatus.CANCELLED:
        raise ValueError("Appointment must be cancelled before recovery")

    stmt = select(WaitingListEntry).where(
        WaitingListEntry.clinic_id == cancelled.clinic_id,
        WaitingListEntry.doctor_id == cancelled.doctor_id,
        WaitingListEntry.service_id == cancelled.service_id,
        WaitingListEntry.status == "ACTIVE",
    )
    entries = db.scalars(stmt.order_by(WaitingListEntry.priority.desc(), WaitingListEntry.created_at)).all()
    results = []
    for entry in entries:
        if entry.patient_id == cancelled.patient_id:
            continue
        reasons = ["Same doctor", "Same service"]
        score = 50 + max(0, min(20, entry.priority))
        if entry.preferred_day:
            if entry.preferred_day != cancelled.start_at.date():
                continue
            score += 20
            reasons.append("Preferred date matches")
        else:
            reasons.append("Flexible date")
        slot_time = cancelled.start_at.time()
        if entry.earliest_time and slot_time < entry.earliest_time:
            continue
        if entry.latest_time and slot_time > entry.latest_time:
            continue
        if entry.earliest_time or entry.latest_time:
            score += 10
            reasons.append("Preferred time window matches")
        conflict = db.scalar(select(Appointment).where(
            Appointment.clinic_id == cancelled.clinic_id,
            Appointment.patient_id == entry.patient_id,
            Appointment.status.in_(ACTIVE),
            Appointment.start_at < cancelled.end_at,
            Appointment.end_at > cancelled.start_at,
        ))
        if conflict:
            continue
        waiting_days = max(0, (datetime.utcnow() - entry.created_at).days)
        score += min(10, waiting_days)
        if waiting_days:
            reasons.append(f"Waiting {waiting_days} day(s)")
        results.append({
            "waiting_list_id": entry.id,
            "patient_id": entry.patient_id,
            "patient_name": entry.patient.full_name,
            "patient_phone": entry.patient.phone,
            "priority_score": min(100, score),
            "reasons": reasons,
            "preferred_day": entry.preferred_day,
            "earliest_time": entry.earliest_time,
            "latest_time": entry.latest_time,
        })
    return sorted(results, key=lambda x: (-x["priority_score"], x["patient_name"]))
