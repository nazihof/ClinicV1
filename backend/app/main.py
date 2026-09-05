from datetime import datetime, timedelta, date, time
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from .database import get_db
from .models import Clinic, Doctor, Service, Patient, DoctorSchedule, Appointment, AppointmentEvent, AppointmentStatus, RiskScore, WaitingListEntry
from .schemas import *
from .booking import validate_entities, ensure_in_schedule, ensure_no_overlap, calculate_end, ACTIVE
from .risk import calculate_appointment_risk, patient_history
from .attention import build_attention_queue
from .recovery import recovery_candidates

app = FastAPI(title="Clinic Front-Desk Intelligence", version="3.0.0-alpha.5")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000","http://127.0.0.1:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def event(db, appointment_id, event_type, details=None):
    db.add(AppointmentEvent(appointment_id=appointment_id, event_type=event_type, details=details))

def appointment_view(a: Appointment):
    return AppointmentView(
        id=a.id, clinic_id=a.clinic_id, doctor_id=a.doctor_id, patient_id=a.patient_id, service_id=a.service_id,
        start_at=a.start_at, end_at=a.end_at, status=a.status,
        patient_name=a.patient.full_name, patient_phone=a.patient.phone,
        doctor_name=a.doctor.name, service_name=a.service.name,
        duration_minutes=a.service.duration_minutes, price=float(a.service.price) if a.service.price is not None else None
    )

@app.get("/health")
def health(): return {"status":"ok","version":"3.0.0-alpha.5"}

@app.post("/clinics", response_model=ClinicOut)
def create_clinic(body: ClinicCreate, db: Session=Depends(get_db)):
    obj=Clinic(**body.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@app.get("/clinics", response_model=list[ClinicOut])
def list_clinics(db: Session=Depends(get_db)): return db.scalars(select(Clinic).order_by(Clinic.name)).all()

@app.patch("/clinics/{clinic_id}", response_model=ClinicOut)
def update_clinic(clinic_id:int, body:ClinicUpdate, db:Session=Depends(get_db)):
    obj=db.get(Clinic,clinic_id)
    if not obj: raise HTTPException(404,"Clinic not found")
    obj.name=body.name.strip(); obj.timezone=body.timezone.strip() or "Asia/Beirut"
    db.commit(); db.refresh(obj); return obj

@app.post("/doctors", response_model=DoctorOut)
def create_doctor(body: DoctorCreate, db: Session=Depends(get_db)):
    if not db.get(Clinic, body.clinic_id): raise HTTPException(404,"Clinic not found")
    obj=Doctor(**body.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@app.get("/doctors", response_model=list[DoctorOut])
def list_doctors(clinic_id:int, db:Session=Depends(get_db)):
    return db.scalars(select(Doctor).where(Doctor.clinic_id==clinic_id).order_by(Doctor.name)).all()

@app.patch("/doctors/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id:int, body:DoctorUpdate, db:Session=Depends(get_db)):
    obj=db.get(Doctor,doctor_id)
    if not obj: raise HTTPException(404,"Doctor not found")
    obj.name=body.name.strip(); obj.specialty=body.specialty.strip() if body.specialty else None
    db.commit(); db.refresh(obj); return obj

@app.post("/services", response_model=ServiceOut)
def create_service(body: ServiceCreate, db: Session=Depends(get_db)):
    if not db.get(Clinic, body.clinic_id): raise HTTPException(404,"Clinic not found")
    if body.duration_minutes <= 0: raise HTTPException(400,"Duration must be greater than zero")
    obj=Service(**body.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@app.get("/services", response_model=list[ServiceOut])
def list_services(clinic_id:int, db:Session=Depends(get_db)):
    return db.scalars(select(Service).where(Service.clinic_id==clinic_id,Service.is_active.is_(True)).order_by(Service.name)).all()

@app.patch("/services/{service_id}", response_model=ServiceOut)
def update_service(service_id:int, body:ServiceUpdate, db:Session=Depends(get_db)):
    obj=db.get(Service,service_id)
    if not obj: raise HTTPException(404,"Service not found")
    if body.duration_minutes <= 0: raise HTTPException(400,"Duration must be greater than zero")
    obj.name=body.name.strip(); obj.duration_minutes=body.duration_minutes; obj.price=body.price
    db.commit(); db.refresh(obj); return obj

@app.post("/patients", response_model=PatientOut)
def create_patient(body: PatientCreate, db: Session=Depends(get_db)):
    existing=db.scalar(select(Patient).where(Patient.clinic_id==body.clinic_id, Patient.phone==body.phone))
    if existing: raise HTTPException(409,"Patient with this phone already exists")
    obj=Patient(**body.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@app.get("/patients", response_model=list[PatientOut])
def search_patients(clinic_id:int, q:str="", limit:int=20, db:Session=Depends(get_db)):
    stmt=select(Patient).where(Patient.clinic_id==clinic_id)
    if q.strip():
        term=f"%{q.strip()}%"
        stmt=stmt.where(or_(Patient.full_name.ilike(term), Patient.phone.ilike(term)))
    return db.scalars(stmt.order_by(Patient.full_name).limit(limit)).all()
@app.get("/patients/{patient_id}/appointments", response_model=list[AppointmentView])
def patient_appointments(patient_id:int, db:Session=Depends(get_db)):
    patient=db.get(Patient,patient_id)
    if not patient: raise HTTPException(404,"Patient not found")
    rows=db.scalars(select(Appointment).where(Appointment.patient_id==patient_id).order_by(Appointment.start_at.desc())).all()
    return [appointment_view(x) for x in rows]

@app.get("/patients/{patient_id}/history", response_model=PatientHistoryOut)
def get_patient_history(patient_id:int, db:Session=Depends(get_db)):
    patient=db.get(Patient,patient_id)
    if not patient: raise HTTPException(404,"Patient not found")
    return patient_history(db,patient_id)

@app.post("/doctors/{doctor_id}/schedule", response_model=ScheduleOut)
def add_schedule(doctor_id:int, body:ScheduleCreate, db:Session=Depends(get_db)):
    doctor=db.get(Doctor,doctor_id)
    if not doctor or doctor.clinic_id!=body.clinic_id: raise HTTPException(404,"Doctor not found in clinic")
    if not 0 <= body.weekday <= 6: raise HTTPException(400,"weekday must be 0-6")
    if body.start_time >= body.end_time: raise HTTPException(400,"Start time must be before end time")
    obj=DoctorSchedule(doctor_id=doctor_id,**body.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@app.get("/doctors/{doctor_id}/schedule", response_model=list[ScheduleOut])
def list_schedule(doctor_id:int, clinic_id:int, db:Session=Depends(get_db)):
    doctor=db.get(Doctor,doctor_id)
    if not doctor or doctor.clinic_id!=clinic_id: raise HTTPException(404,"Doctor not found in clinic")
    return db.scalars(select(DoctorSchedule).where(DoctorSchedule.clinic_id==clinic_id,DoctorSchedule.doctor_id==doctor_id).order_by(DoctorSchedule.weekday,DoctorSchedule.start_time)).all()

@app.patch("/schedules/{schedule_id}", response_model=ScheduleOut)
def update_schedule(schedule_id:int, body:ScheduleUpdate, db:Session=Depends(get_db)):
    obj=db.get(DoctorSchedule,schedule_id)
    if not obj: raise HTTPException(404,"Schedule not found")
    if not 0 <= body.weekday <= 6: raise HTTPException(400,"weekday must be 0-6")
    if body.start_time >= body.end_time: raise HTTPException(400,"Start time must be before end time")
    obj.weekday=body.weekday; obj.start_time=body.start_time; obj.end_time=body.end_time
    db.commit(); db.refresh(obj); return obj

@app.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id:int, db:Session=Depends(get_db)):
    obj=db.get(DoctorSchedule,schedule_id)
    if not obj: raise HTTPException(404,"Schedule not found")
    db.delete(obj); db.commit(); return {"deleted":True,"id":schedule_id}

@app.get("/doctors/{doctor_id}/availability", response_model=list[AvailabilitySlot])
def availability(doctor_id:int, clinic_id:int, service_id:int, day:date, db:Session=Depends(get_db)):
    service=db.get(Service,service_id)
    if not service or service.clinic_id!=clinic_id: raise HTTPException(404,"Service not found")
    schedules=db.scalars(select(DoctorSchedule).where(DoctorSchedule.clinic_id==clinic_id,DoctorSchedule.doctor_id==doctor_id,DoctorSchedule.weekday==day.weekday())).all()
    slots=[]
    for s in schedules:
        cursor=datetime.combine(day,s.start_time)
        end_of_schedule=datetime.combine(day,s.end_time)
        while cursor+timedelta(minutes=service.duration_minutes)<=end_of_schedule:
            end=cursor+timedelta(minutes=service.duration_minutes)
            conflict=db.scalar(select(Appointment).where(Appointment.clinic_id==clinic_id,Appointment.doctor_id==doctor_id,Appointment.status.in_(ACTIVE),Appointment.start_at<end,Appointment.end_at>cursor))
            if not conflict: slots.append(AvailabilitySlot(start_at=cursor,end_at=end))
            cursor += timedelta(minutes=15)
    return slots

@app.post("/appointments", response_model=AppointmentOut)
def create_appointment(body:AppointmentCreate, db:Session=Depends(get_db)):
    _,_,service=validate_entities(db,body.clinic_id,body.doctor_id,body.patient_id,body.service_id)
    end=calculate_end(body.start_at,service.duration_minutes)
    ensure_in_schedule(db,body.clinic_id,body.doctor_id,body.start_at,end)
    ensure_no_overlap(db,body.clinic_id,body.doctor_id,body.start_at,end)
    obj=Appointment(**body.model_dump(),end_at=end,status=AppointmentStatus.PENDING)
    db.add(obj); db.flush(); event(db,obj.id,"CREATED"); db.commit(); db.refresh(obj); return obj

@app.get("/appointments", response_model=list[AppointmentView])
def list_appointments(clinic_id:int, day:date|None=None, doctor_id:int|None=None, db:Session=Depends(get_db)):
    stmt=select(Appointment).where(Appointment.clinic_id==clinic_id)
    if day:
        start=datetime.combine(day,time.min); end=start+timedelta(days=1)
        stmt=stmt.where(Appointment.start_at>=start,Appointment.start_at<end)
    if doctor_id: stmt=stmt.where(Appointment.doctor_id==doctor_id)
    rows=db.scalars(stmt.order_by(Appointment.start_at)).all()
    return [appointment_view(x) for x in rows]

@app.get("/appointments/{appointment_id}", response_model=AppointmentView)
def get_appointment(appointment_id:int, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    return appointment_view(a)

def transition(db,a,status,event_name):
    a.status=status; event(db,a.id,event_name); db.commit(); db.refresh(a); return a

@app.patch("/appointments/{appointment_id}/confirm", response_model=AppointmentOut)
def confirm(appointment_id:int, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    return transition(db,a,AppointmentStatus.CONFIRMED,"CONFIRMED")
@app.patch("/appointments/{appointment_id}/check-in", response_model=AppointmentOut)
def check_in(appointment_id:int, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    return transition(db,a,AppointmentStatus.CHECKED_IN,"CHECKED_IN")
@app.patch("/appointments/{appointment_id}/complete", response_model=AppointmentOut)
def complete(appointment_id:int, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    return transition(db,a,AppointmentStatus.COMPLETED,"COMPLETED")
@app.patch("/appointments/{appointment_id}/no-show", response_model=AppointmentOut)
def no_show(appointment_id:int, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    return transition(db,a,AppointmentStatus.NO_SHOW,"NO_SHOW")
@app.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(appointment_id:int, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    return transition(db,a,AppointmentStatus.CANCELLED,"CANCELLED")
@app.patch("/appointments/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule(appointment_id:int, body:AppointmentReschedule, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    service=db.get(Service,a.service_id); end=calculate_end(body.start_at,service.duration_minutes)
    ensure_in_schedule(db,a.clinic_id,a.doctor_id,body.start_at,end)
    ensure_no_overlap(db,a.clinic_id,a.doctor_id,body.start_at,end,exclude_id=a.id)
    old=a.start_at; a.start_at=body.start_at; a.end_at=end; a.status=AppointmentStatus.PENDING
    event(db,a.id,"RESCHEDULED",f"{old.isoformat()} -> {body.start_at.isoformat()}")
    db.commit(); db.refresh(a); return a

@app.get("/appointments/{appointment_id}/risk", response_model=RiskOut)
def appointment_risk(appointment_id:int, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    result=calculate_appointment_risk(db,a,persist=True)
    db.commit()
    return {"appointment_id":a.id,"patient_id":a.patient_id,**result}

@app.post("/risk/recalculate")
def recalculate_risk(clinic_id:int, db:Session=Depends(get_db)):
    rows=db.scalars(select(Appointment).where(Appointment.clinic_id==clinic_id,Appointment.status.in_([AppointmentStatus.PENDING,AppointmentStatus.CONFIRMED]))).all()
    updated=[]
    for a in rows:
        r=calculate_appointment_risk(db,a,persist=True)
        updated.append({"appointment_id":a.id,"score":r["score"],"level":r["level"]})
    db.commit()
    return {"updated":len(updated),"appointments":updated}

@app.get("/appointments/{appointment_id}/events", response_model=list[EventOut])
def events(appointment_id:int, db:Session=Depends(get_db)):
    return db.scalars(select(AppointmentEvent).where(AppointmentEvent.appointment_id==appointment_id).order_by(AppointmentEvent.created_at)).all()



def waiting_view(x: WaitingListEntry):
    return WaitingListView(
        id=x.id, clinic_id=x.clinic_id, patient_id=x.patient_id, doctor_id=x.doctor_id, service_id=x.service_id,
        preferred_day=x.preferred_day, earliest_time=x.earliest_time, latest_time=x.latest_time, priority=x.priority,
        status=x.status, notes=x.notes, created_at=x.created_at, patient_name=x.patient.full_name,
        patient_phone=x.patient.phone, doctor_name=x.doctor.name, service_name=x.service.name
    )

@app.post("/waiting-list", response_model=WaitingListView)
def add_waiting_list(body: WaitingListCreate, db:Session=Depends(get_db)):
    patient, doctor, service = validate_entities(db, body.clinic_id, body.doctor_id, body.patient_id, body.service_id)
    if body.earliest_time and body.latest_time and body.earliest_time > body.latest_time:
        raise HTTPException(400, "Earliest time must be before latest time")
    existing=db.scalar(select(WaitingListEntry).where(
        WaitingListEntry.clinic_id==body.clinic_id, WaitingListEntry.patient_id==body.patient_id,
        WaitingListEntry.doctor_id==body.doctor_id, WaitingListEntry.service_id==body.service_id,
        WaitingListEntry.status=="ACTIVE"
    ))
    if existing:
        raise HTTPException(409, "Patient already has an active waiting-list request for this doctor and service")
    obj=WaitingListEntry(**body.model_dump(), status="ACTIVE")
    db.add(obj); db.commit(); db.refresh(obj); return waiting_view(obj)

@app.get("/waiting-list", response_model=list[WaitingListView])
def list_waiting_list(clinic_id:int, doctor_id:int|None=None, status:str="ACTIVE", db:Session=Depends(get_db)):
    stmt=select(WaitingListEntry).where(WaitingListEntry.clinic_id==clinic_id)
    if doctor_id: stmt=stmt.where(WaitingListEntry.doctor_id==doctor_id)
    if status: stmt=stmt.where(WaitingListEntry.status==status.upper())
    rows=db.scalars(stmt.order_by(WaitingListEntry.priority.desc(),WaitingListEntry.created_at)).all()
    return [waiting_view(x) for x in rows]

@app.delete("/waiting-list/{waiting_id}")
def remove_waiting_list(waiting_id:int, db:Session=Depends(get_db)):
    obj=db.get(WaitingListEntry,waiting_id)
    if not obj: raise HTTPException(404,"Waiting-list entry not found")
    if obj.status!="ACTIVE": raise HTTPException(409,"Only active waiting-list entries can be removed")
    obj.status="REMOVED"; db.commit(); return {"removed":True,"id":waiting_id}

@app.get("/appointments/{appointment_id}/recovery-candidates", response_model=list[RecoveryCandidateOut])
def get_recovery_candidates(appointment_id:int, db:Session=Depends(get_db)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    if a.status!=AppointmentStatus.CANCELLED: raise HTTPException(409,"Appointment must be cancelled before recovery")
    return recovery_candidates(db,a)

@app.post("/appointments/{appointment_id}/recover/{waiting_id}", response_model=RecoveryResultOut)
def recover_cancelled_slot(appointment_id:int, waiting_id:int, db:Session=Depends(get_db)):
    cancelled=db.get(Appointment,appointment_id)
    if not cancelled: raise HTTPException(404,"Cancelled appointment not found")
    if cancelled.status!=AppointmentStatus.CANCELLED: raise HTTPException(409,"Appointment is not cancelled")
    entry=db.get(WaitingListEntry,waiting_id)
    if not entry or entry.status!="ACTIVE": raise HTTPException(404,"Active waiting-list entry not found")
    candidates={x["waiting_list_id"]:x for x in recovery_candidates(db,cancelled)}
    if waiting_id not in candidates: raise HTTPException(409,"Waiting-list patient is not eligible for this cancelled slot")
    ensure_no_overlap(db,cancelled.clinic_id,cancelled.doctor_id,cancelled.start_at,cancelled.end_at)
    new=Appointment(clinic_id=cancelled.clinic_id,doctor_id=cancelled.doctor_id,patient_id=entry.patient_id,
                    service_id=cancelled.service_id,start_at=cancelled.start_at,end_at=cancelled.end_at,status=AppointmentStatus.PENDING)
    db.add(new); db.flush()
    event(db,new.id,"CREATED_FROM_WAITLIST",f"Recovered cancelled appointment {cancelled.id}; waiting-list entry {entry.id}")
    event(db,cancelled.id,"SLOT_RECOVERED",f"Replacement appointment {new.id}; waiting-list entry {entry.id}")
    entry.status="BOOKED"
    db.commit(); db.refresh(new)
    return {"cancelled_appointment_id":cancelled.id,"new_appointment_id":new.id,"waiting_list_id":entry.id,
            "patient_id":entry.patient_id,"start_at":new.start_at,"status":new.status.value}

@app.get("/attention-queue", response_model=AttentionQueueOut)
def attention_queue(clinic_id:int, day:date, doctor_id:int|None=None, db:Session=Depends(get_db)):
    if not db.get(Clinic, clinic_id):
        raise HTTPException(404, "Clinic not found")
    result=build_attention_queue(db, clinic_id, day, doctor_id=doctor_id)
    db.commit()
    return result

@app.get("/dashboard/summary")
def dashboard_summary(clinic_id:int, day:date, doctor_id:int|None=None, db:Session=Depends(get_db)):
    start=datetime.combine(day,time.min); end=start+timedelta(days=1)
    stmt=select(Appointment).where(Appointment.clinic_id==clinic_id,Appointment.start_at>=start,Appointment.start_at<end)
    if doctor_id: stmt=stmt.where(Appointment.doctor_id==doctor_id)
    appts=db.scalars(stmt).all()
    counts={s.value:0 for s in AppointmentStatus}
    risk_counts={"LOW":0,"MEDIUM":0,"HIGH":0}
    risks={}
    for a in appts:
        counts[a.status.value]+=1
        if a.status in (AppointmentStatus.PENDING,AppointmentStatus.CONFIRMED):
            r=calculate_appointment_risk(db,a,persist=True)
            risks[a.id]=r
            risk_counts[r["level"]]+=1
    queue=build_attention_queue(db, clinic_id, day, doctor_id=doctor_id)
    db.commit()
    return {"total":len(appts),"counts":counts,"risk_counts":risk_counts,"attention":queue["items"][:12],"attention_counts":queue["counts"]}


@app.get("/dashboard/operational")
def operational_dashboard(
    clinic_id:int,
    start_day:date,
    end_day:date,
    doctor_id:int|None=None,
    db:Session=Depends(get_db),
):
    """Operational KPIs only. Revenue analytics are intentionally deferred beyond Sprint 3G."""
    if not db.get(Clinic, clinic_id):
        raise HTTPException(404, "Clinic not found")
    if start_day > end_day:
        raise HTTPException(400, "start_day must be on or before end_day")
    if (end_day-start_day).days > 366:
        raise HTTPException(400, "Operational dashboard range cannot exceed 366 days")
    if doctor_id:
        doctor=db.get(Doctor, doctor_id)
        if not doctor or doctor.clinic_id != clinic_id:
            raise HTTPException(404, "Doctor not found in this clinic")

    start=datetime.combine(start_day,time.min)
    end=datetime.combine(end_day+timedelta(days=1),time.min)
    stmt=select(Appointment).where(
        Appointment.clinic_id==clinic_id,
        Appointment.start_at>=start,
        Appointment.start_at<end,
    )
    if doctor_id:
        stmt=stmt.where(Appointment.doctor_id==doctor_id)
    appts=list(db.scalars(stmt.order_by(Appointment.start_at)).all())

    counts={s.value:0 for s in AppointmentStatus}
    for a in appts:
        counts[a.status.value]+=1
    total=len(appts)
    completed=counts[AppointmentStatus.COMPLETED.value]
    no_show=counts[AppointmentStatus.NO_SHOW.value]
    cancelled=counts[AppointmentStatus.CANCELLED.value]
    pending=counts[AppointmentStatus.PENDING.value]
    confirmed=counts[AppointmentStatus.CONFIRMED.value]
    checked_in=counts[AppointmentStatus.CHECKED_IN.value]
    attended_outcomes=completed+no_show

    # Recovery is operational rather than financial: a cancelled slot counts as recovered
    # only when SLOT_RECOVERED was recorded for that cancelled appointment.
    appointment_ids=[a.id for a in appts]
    recovered_ids=set()
    if appointment_ids:
        recovered_ids=set(db.scalars(
            select(AppointmentEvent.appointment_id).where(
                AppointmentEvent.appointment_id.in_(appointment_ids),
                AppointmentEvent.event_type=="SLOT_RECOVERED",
            )
        ).all())
    recovered_cancelled=sum(1 for a in appts if a.status==AppointmentStatus.CANCELLED and a.id in recovered_ids)

    active_wait_stmt=select(func.count()).select_from(WaitingListEntry).where(
        WaitingListEntry.clinic_id==clinic_id, WaitingListEntry.status=="ACTIVE"
    )
    if doctor_id:
        active_wait_stmt=active_wait_stmt.where(WaitingListEntry.doctor_id==doctor_id)
    active_waiting=int(db.scalar(active_wait_stmt) or 0)

    # Risk mix for active appointments in the selected period.
    risk_counts={"LOW":0,"MEDIUM":0,"HIGH":0}
    for a in appts:
        if a.status in (AppointmentStatus.PENDING,AppointmentStatus.CONFIRMED):
            r=calculate_appointment_risk(db,a,persist=True)
            risk_counts[r["level"]]+=1

    # Daily trend.
    by_day={}
    cursor=start_day
    while cursor<=end_day:
        by_day[cursor.isoformat()]={"day":cursor.isoformat(),"total":0,"completed":0,"cancelled":0,"no_show":0}
        cursor+=timedelta(days=1)
    for a in appts:
        row=by_day[a.start_at.date().isoformat()]
        row["total"]+=1
        if a.status==AppointmentStatus.COMPLETED: row["completed"]+=1
        elif a.status==AppointmentStatus.CANCELLED: row["cancelled"]+=1
        elif a.status==AppointmentStatus.NO_SHOW: row["no_show"]+=1

    # Doctor breakdown for operational comparison, never revenue.
    doctors_by_id={d.id:d for d in db.scalars(select(Doctor).where(Doctor.clinic_id==clinic_id)).all()}
    doctor_rows={}
    for a in appts:
        row=doctor_rows.setdefault(a.doctor_id,{
            "doctor_id":a.doctor_id,
            "doctor_name":doctors_by_id.get(a.doctor_id).name if doctors_by_id.get(a.doctor_id) else f"Doctor {a.doctor_id}",
            "total":0,"completed":0,"cancelled":0,"no_show":0,
        })
        row["total"]+=1
        if a.status==AppointmentStatus.COMPLETED: row["completed"]+=1
        elif a.status==AppointmentStatus.CANCELLED: row["cancelled"]+=1
        elif a.status==AppointmentStatus.NO_SHOW: row["no_show"]+=1
    for row in doctor_rows.values():
        outcome=row["completed"]+row["no_show"]
        row["no_show_rate_percent"]=round((row["no_show"]/outcome*100) if outcome else 0,1)
        row["completion_rate_percent"]=round((row["completed"]/row["total"]*100) if row["total"] else 0,1)

    lead_hours=[]
    for a in appts:
        if a.created_at and a.start_at>=a.created_at:
            lead_hours.append((a.start_at-a.created_at).total_seconds()/3600)

    db.commit()
    return {
        "period":{"start_day":start_day,"end_day":end_day,"days":(end_day-start_day).days+1},
        "total_appointments":total,
        "counts":counts,
        "rates":{
            "completion_rate_percent":round((completed/total*100) if total else 0,1),
            "no_show_rate_percent":round((no_show/attended_outcomes*100) if attended_outcomes else 0,1),
            "cancellation_rate_percent":round((cancelled/total*100) if total else 0,1),
            "confirmation_open_percent":round((pending/(pending+confirmed)*100) if (pending+confirmed) else 0,1),
            "cancellation_recovery_rate_percent":round((recovered_cancelled/cancelled*100) if cancelled else 0,1),
        },
        "operations":{
            "recovered_cancelled_slots":recovered_cancelled,
            "unrecovered_cancelled_slots":max(cancelled-recovered_cancelled,0),
            "active_waiting_list":active_waiting,
            "average_booking_lead_hours":round(sum(lead_hours)/len(lead_hours),1) if lead_hours else 0,
            "open_workflow":pending+confirmed+checked_in,
        },
        "risk_counts":risk_counts,
        "daily_trend":list(by_day.values()),
        "doctor_breakdown":sorted(doctor_rows.values(),key=lambda x:(-x["total"],x["doctor_name"])),
        "revenue_metrics_included":False,
    }
