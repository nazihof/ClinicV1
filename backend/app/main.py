from datetime import datetime, timedelta, date,timezone,time
import os
import time as pytime
import hashlib
import hmac
import httpx
from collections import defaultdict, deque
from threading import Lock
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import Session
from .database import get_db, SessionLocal
from .models import Clinic, Doctor, Service, Patient, DoctorSchedule, Appointment, AppointmentEvent, AppointmentStatus, RiskScore, WaitingListEntry, User, UserRole, AuditLog,WhatsAppChannel, Conversation, Message
from .schemas import *
from .booking import validate_entities, ensure_in_schedule, ensure_no_overlap, calculate_end, ACTIVE
from .risk import calculate_appointment_risk, patient_history
from .attention import build_attention_queue
from .recovery import recovery_candidates
from .auth import hash_password, verify_password, make_token, decode_token

app = FastAPI(title="Clinic Front-Desk Intelligence", version="4.5.4-pilot.1")



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


PUBLIC_PATHS={"/health","/ready","/auth/status","/auth/setup-clinics","/auth/setup","/auth/login","/docs","/openapi.json","/redoc","/whatsapp/webhook"}

def _deny(detail="Access denied", status=403):
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail":detail}, status_code=status)

def _role_value(user):
    return user.role.value if hasattr(user.role, "value") else str(user.role)

def _doctor_related_patient(db, patient_id:int, doctor_id:int)->bool:
    return db.scalar(select(func.count(Appointment.id)).where(Appointment.patient_id==patient_id, Appointment.doctor_id==doctor_id)) > 0

async def send_whatsapp_text(
    phone_number_id: str,
    recipient: str,
    message_body: str,
):
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN is not configured")

    url = (
        f"https://graph.facebook.com/v23.0/"
        f"{phone_number_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {
            "body": message_body,
        },
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        raise RuntimeError(
            f"WhatsApp API error "
            f"{response.status_code}: {response.text}"
        )

    return response.json()

# Sprint 4.5C: pilot-grade abuse protection. This is intentionally simple and
# process-local; for horizontally scaled production use Redis or an API gateway.
_RATE_BUCKETS = defaultdict(deque)
_RATE_LOCK = Lock()

def _client_ip(request: Request) -> str:
    trust_proxy = os.getenv("TRUST_PROXY", "false").lower() in {"1","true","yes"}
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "unknown")[:64]

def _limited(key: str, limit: int, window_seconds: int) -> bool:
    now = pytime.monotonic()
    with _RATE_LOCK:
        q = _RATE_BUCKETS[key]
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= limit:
            return True
        q.append(now)
        return False

def _apply_security_headers(response, request: Request):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if request.url.path.startswith("/auth/"):
        response.headers["Cache-Control"] = "no-store"
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if os.getenv("APP_ENV", "development").lower() == "production" and forwarded_proto == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

def _write_audit(request: Request, response):
    path = request.url.path
    user_state = getattr(request.state, "user", None)
    public_security_action = path in {"/auth/login", "/auth/setup"} and request.method == "POST"
    authenticated_write = bool(user_state) and request.method in {"POST","PATCH","PUT","DELETE"}
    if not (public_security_action or authenticated_write):
        return
    action = ("AUTH_LOGIN" if path == "/auth/login" else "AUTH_SETUP" if path == "/auth/setup" else f"{request.method} {path}")
    try:
        with SessionLocal() as db:
            db.add(AuditLog(
                clinic_id=int(user_state["clinic_id"]) if user_state else None,
                user_id=int(user_state["sub"]) if user_state else None,
                action=action, method=request.method, path=path[:255],
                status_code=int(response.status_code), ip_address=_client_ip(request),
                user_agent=(request.headers.get("user-agent") or "")[:255] or None,
            ))
            db.commit()
    except Exception as exc:
        # Audit failure must not break front-desk work, but it remains visible in server logs.
        print(f"AUDIT_LOG_WRITE_FAILED: {exc}")

@app.middleware("http")
async def security_rate_limit_and_audit(request: Request, call_next):
    ip = _client_ip(request)
   
    # Public webhook endpoint for Meta verification/events
    if request.url.path == "/whatsapp/webhook":
    	response = await call_next(request)
    	return _apply_security_headers(response, request)

# existing authentication logic continues below
   # if not user:
    #	return _deny("Authentication required", 401)

    if request.url.path == "/auth/login" and request.method == "POST":
        if _limited(f"login:{ip}", int(os.getenv("LOGIN_RATE_LIMIT", "8")), 60):
            response = _deny("Too many login attempts. Try again shortly.", 429)
            response.headers["Retry-After"] = "60"
            return _apply_security_headers(response, request)
    if request.url.path == "/auth/setup" and request.method == "POST":
        if _limited(f"setup:{ip}", 5, 300):
            response = _deny("Too many setup attempts. Try again later.", 429)
            response.headers["Retry-After"] = "300"
            return _apply_security_headers(response, request)
    response = await call_next(request)
    _write_audit(request, response)
    return _apply_security_headers(response, request)


@app.middleware("http")
async def authentication_gate(request:Request, call_next):
    path=request.url.path
    if request.method=="OPTIONS" or path in PUBLIC_PATHS:
        return await call_next(request)
    auth=request.headers.get("Authorization","")
    if not auth.startswith("Bearer "):
        return _deny("Authentication required",401)
    try:
        claims=decode_token(auth[7:])
    except HTTPException as e:
        return _deny(e.detail,e.status_code)

    with SessionLocal() as db:
        user=db.get(User,int(claims.get("sub",0)))
        if not user or not user.is_active:
            return _deny("User unavailable",401)
        if int(claims.get("clinic_id",-1)) != user.clinic_id or claims.get("role") != _role_value(user):
            return _deny("Authentication claims are stale; sign in again",401)
        request.state.user={"sub":str(user.id),"clinic_id":user.clinic_id,"role":_role_value(user),"doctor_id":user.doctor_id}

        qclinic=request.query_params.get("clinic_id")
        if qclinic and int(qclinic)!=user.clinic_id:
            return _deny("Clinic access denied")

        # Path-parameter tenant isolation. Collection routes are constrained by query/body checks.
        parts=[x for x in path.split("/") if x]
        if len(parts)>=2 and parts[1].isdigit():
            entity_id=int(parts[1]); entity=None
            if parts[0]=="clinics": entity=db.get(Clinic,entity_id)
            elif parts[0]=="doctors": entity=db.get(Doctor,entity_id)
            elif parts[0]=="patients": entity=db.get(Patient,entity_id)
            elif parts[0]=="schedules": entity=db.get(DoctorSchedule,entity_id)
            elif parts[0]=="appointments": entity=db.get(Appointment,entity_id)
            elif parts[0]=="waiting-list": entity=db.get(WaitingListEntry,entity_id)
            elif parts[0]=="users": entity=db.get(User,entity_id)
            if entity is not None and getattr(entity,"clinic_id",user.clinic_id)!=user.clinic_id:
                return _deny("Clinic access denied")

        role=_role_value(user)
        if role=="SECRETARY":
            # Secretaries operate the front desk but cannot alter clinic configuration or user access.
            config_write=(request.method in {"POST","PATCH","DELETE"} and (
                path=="/clinics" or path.startswith("/clinics/") or path=="/doctors" or
                (path.startswith("/doctors/") and path.endswith("/schedule")) or path=="/services" or
                path.startswith("/services/") or path.startswith("/schedules/") or path.startswith("/users")
            ))
            if config_write: return _deny("OWNER role required")
        elif role=="DOCTOR":
            # Doctor accounts are intentionally read-only in the front-desk pilot.
            if request.method!="GET": return _deny("Doctor access is read-only")
            if path.startswith("/waiting-list") or path.startswith("/users") or path=="/patients":
                return _deny("Doctor access denied")
            did=user.doctor_id
            if not did: return _deny("Doctor account is not linked to a doctor profile")
            qdoctor=request.query_params.get("doctor_id")
            if qdoctor and int(qdoctor)!=did: return _deny("Doctor scope denied")
            if len(parts)>=2 and parts[0]=="doctors" and parts[1].isdigit() and int(parts[1])!=did:
                return _deny("Doctor scope denied")
            if len(parts)>=2 and parts[0]=="appointments" and parts[1].isdigit():
                a=db.get(Appointment,int(parts[1]))
                if a and a.doctor_id!=did: return _deny("Doctor scope denied")
            if len(parts)>=2 and parts[0]=="patients" and parts[1].isdigit() and not _doctor_related_patient(db,int(parts[1]),did):
                return _deny("Patient scope denied")
            if path.startswith("/dashboard") or path=="/attention-queue" or path=="/appointments":
                if not qdoctor or int(qdoctor)!=did: return _deny("Doctor scope requires doctor_id")

    return await call_next(request)

def _cors_origins():
    raw = os.getenv("CORS_ORIGINS","http://localhost:3000,http://127.0.0.1:3000")
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]

app.add_middleware(CORSMiddleware, allow_origins=_cors_origins(), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/whatsapp/webhook", response_class=PlainTextResponse)
def whatsapp_webhook_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

    if (
        hub_mode == "subscribe"
        and expected_token
        and hub_verify_token == expected_token
    ):
        return hub_challenge

    raise HTTPException(
        status_code=403,
        detail="Webhook verification failed",
    )

@app.post("/whatsapp/webhook")
async def whatsapp_webhook_receive(
    request: Request,
    db: Session = Depends(get_db),
):
    app_secret = os.getenv("WHATSAPP_APP_SECRET")

    if not app_secret:
        raise HTTPException(
            status_code=500,
            detail="WhatsApp app secret is not configured",
        )

    raw_body = await request.body()

    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        print("WHATSAPP SIGNATURE CHECK: MISSING")
        raise HTTPException(
            status_code=401,
            detail="Missing WhatsApp webhook signature",
        )

    expected_signature = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        signature_header,
        expected_signature,
    ):
        print("WHATSAPP SIGNATURE CHECK: INVALID")
        raise HTTPException(
            status_code=401,
            detail="Invalid WhatsApp webhook signature",
        )

    payload = await request.json()

    try:
        entries = payload.get("entry", [])

        for entry in entries:
            changes = entry.get("changes", [])

            for change in changes:
                value = change.get("value", {})
		# -------------------------------------------------
		# Process WhatsApp delivery/read status updates
		# -------------------------------------------------

                statuses = value.get("statuses", [])

            for status_item in statuses:
                provider_message_id = status_item.get("id")
                meta_status = status_item.get("status")

                if not provider_message_id or not meta_status:
                    continue

                message = db.scalar(
                    select(Message).where(
                        Message.provider_message_id == provider_message_id
                    )
                )

                if not message:
                    print(
                        "WHATSAPP STATUS: message not found:",
                        provider_message_id
                    )
                    continue

                status_map = {
                    "sent": "SENT",
                    "delivered": "DELIVERED",
                    "read": "READ",
                    "failed": "FAILED",
                }

                new_status = status_map.get(meta_status.lower())

                if not new_status:
                    print(
                        "WHATSAPP STATUS: unsupported status:",
                        meta_status
                    )
                    continue

                message.status = new_status

                print(
                    f"WHATSAPP STATUS UPDATED "
                    f"message={message.id} "
                    f"status={new_status}"
                )

            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")

            if not phone_number_id:
                continue

            # Determine which clinic owns this WhatsApp number
            channel = db.scalar(
                select(WhatsAppChannel).where(
                    WhatsAppChannel.phone_number_id == phone_number_id,
                    WhatsAppChannel.is_active == True,
                )
            )

            if not channel:
                print(
                    "WHATSAPP: unknown phone_number_id:",
                    phone_number_id
                )
                continue

            contacts = value.get("contacts", [])
            contact_names = {}

            for contact in contacts:
                wa_id = contact.get("wa_id")
                profile = contact.get("profile", {})

                if wa_id:
                    contact_names[wa_id] = profile.get("name")

            messages = value.get("messages", [])

            for incoming in messages:
                provider_message_id = incoming.get("id")
                wa_contact_id = incoming.get("from")

                if not provider_message_id or not wa_contact_id:
                    continue

                existing_message = db.scalar(
                    select(Message).where(
                        Message.provider_message_id == provider_message_id
                    )
                )

                if existing_message:
                    continue

                conversation = db.scalar(
                    select(Conversation).where(
                        Conversation.whatsapp_channel_id == channel.id,
                        Conversation.wa_contact_id == wa_contact_id,
                    )
                )

                timestamp_raw = incoming.get("timestamp")
                provider_timestamp = None

                if timestamp_raw:
                    try:
                        provider_timestamp = datetime.fromtimestamp(
                            int(timestamp_raw),
                            tz=timezone.utc,
                        )
                    except (ValueError, TypeError):
                        pass

                if not conversation:
                    conversation = Conversation(
                        clinic_id=channel.clinic_id,
                        whatsapp_channel_id=channel.id,
                        wa_contact_id=wa_contact_id,
                        contact_name=contact_names.get(wa_contact_id),
                        status="OPEN",
                        last_message_at=provider_timestamp,
                    )

                    db.add(conversation)
                    db.flush()

                else:
                    if contact_names.get(wa_contact_id):
                        conversation.contact_name = contact_names[wa_contact_id]

                    conversation.last_message_at = (
                        provider_timestamp
                        or datetime.now(timezone.utc)
                    )

                message_type = incoming.get("type", "unknown")
                body = None

                if message_type == "text":
                    body = incoming.get("text", {}).get("body")

                message = Message(
                    clinic_id=channel.clinic_id,
                    conversation_id=conversation.id,
                    provider_message_id=provider_message_id,
                    direction="INBOUND",
                    message_type=message_type,
                    body=body,
                    status="RECEIVED",
                    provider_timestamp=provider_timestamp,
                )

                db.add(message)

                print(
                    f"WHATSAPP STORED clinic={channel.clinic_id} "
                    f"conversation={conversation.id} "
                    f"from={wa_contact_id} "
                    f"type={message_type}"
                )

        db.commit()

    except Exception as exc:
        db.rollback()
        print("WHATSAPP WEBHOOK ERROR:", repr(exc))

        # For now expose the failure while testing.
        raise HTTPException(
            status_code=500,
            detail="WhatsApp webhook processing failed",
        )

    return {"status": "ok"}


@app.post("/whatsapp/send")
async def whatsapp_send_message(
    data: WhatsAppSendRequest,
    db: Session = Depends(get_db),
):
    # 1. Find the WhatsApp channel / clinic
    channel = db.scalar(
        select(WhatsAppChannel).where(
            WhatsAppChannel.phone_number_id == data.phone_number_id,
            WhatsAppChannel.is_active == True,
        )
    )

    if not channel:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp channel not found",
        )

    # 2. Find or create conversation for recipient
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.whatsapp_channel_id == channel.id,
            Conversation.wa_contact_id == data.recipient,
        )
    )

    if not conversation:
        conversation = Conversation(
            clinic_id=channel.clinic_id,
            whatsapp_channel_id=channel.id,
            wa_contact_id=data.recipient,
            status="OPEN",
            last_message_at=datetime.now(timezone.utc),
        )

        db.add(conversation)
        db.flush()

    try:
        # 3. Send message through Meta
        result = await send_whatsapp_text(
            phone_number_id=data.phone_number_id,
            recipient=data.recipient,
            message_body=data.message,
        )

        # 4. Extract Meta message ID
        messages = result.get("messages", [])

        if not messages or not messages[0].get("id"):
            raise RuntimeError(
                "Meta accepted request but returned no message ID"
            )

        provider_message_id = messages[0]["id"]

        # 5. Store outgoing message
        outbound_message = Message(
            clinic_id=channel.clinic_id,
            conversation_id=conversation.id,
            provider_message_id=provider_message_id,
            direction="OUTBOUND",
            message_type="text",
            body=data.message,
            status="SENT",
            provider_timestamp=datetime.now(timezone.utc),
        )

        db.add(outbound_message)

        conversation.last_message_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "status": "sent",
            "message_id": provider_message_id,
            "conversation_id": conversation.id,
            "provider_response": result,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )


async def whatsapp_send_message(
    data: WhatsAppSendRequest,
):
    try:
        result = await send_whatsapp_text(
            phone_number_id=data.phone_number_id,
            recipient=data.recipient,
            message_body=data.message,
        )

        return {
            "status": "sent",
            "provider_response": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )
@app.get(
    "/whatsapp/conversations",
    response_model=list[WhatsAppConversationOut],
)
def whatsapp_list_conversations(
    request: Request,
    db: Session = Depends(get_db),
):
    clinic_id = int(request.state.user["clinic_id"])

    conversations = db.scalars(
        select(Conversation)
        .where(
            Conversation.clinic_id == clinic_id
        )
        .order_by(
            Conversation.last_message_at.desc().nullslast(),
            Conversation.id.desc(),
        )
    ).all()

    return conversations

@app.get(
    "/whatsapp/conversations/{conversation_id}/messages",
    response_model=list[WhatsAppMessageOut],
)
def whatsapp_conversation_messages(
    conversation_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    clinic_id = int(request.state.user["clinic_id"])

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.clinic_id == clinic_id,
        )
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    messages = db.scalars(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.clinic_id == clinic_id,
        )
        .order_by(
            Message.created_at.asc(),
            Message.id.asc(),
        )
    ).all()

    return messages

@app.get("/ready")
def readiness(db:Session=Depends(get_db)):
    """Pilot readiness probe: verifies database access and expected Alembic revision."""
    expected_revision = "0006_audit_logs"
    try:
        db.execute(text("SELECT 1"))
        current_revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database not ready: {exc}")
    if current_revision != expected_revision:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Database migration is not at the expected revision",
                "expected": expected_revision,
                "current": current_revision,
            },
        )
    return {"status":"ready","database":"ok","alembic":current_revision,"version":"4.5.4-pilot.1"}

@app.get("/auth/status")
def auth_status(db:Session=Depends(get_db)):
    return {"setup_required":db.scalar(select(func.count(User.id)))==0,"clinic_count":db.scalar(select(func.count(Clinic.id))) or 0}

@app.get("/auth/setup-clinics",response_model=list[ClinicOut])
def setup_clinics(db:Session=Depends(get_db)):
    if db.scalar(select(func.count(User.id)))!=0: raise HTTPException(403,"Setup already completed")
    return db.scalars(select(Clinic).order_by(Clinic.name)).all()

@app.post("/auth/setup",response_model=TokenOut)
def auth_setup(body:SetupOwner,db:Session=Depends(get_db)):
    if db.scalar(select(func.count(User.id)))!=0: raise HTTPException(409,"Initial owner already configured")
    clinic=None
    if body.clinic_id is not None:
        clinic=db.get(Clinic,body.clinic_id)
        if not clinic: raise HTTPException(404,"Clinic not found")
    else:
        name=(body.clinic_name or "").strip()
        if not name: raise HTTPException(400,"Clinic name is required for a fresh installation")
        clinic=Clinic(name=name,timezone=(body.timezone or "Asia/Beirut").strip() or "Asia/Beirut")
        db.add(clinic); db.flush()
    email=body.email.strip().lower()
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,"Email already exists")
    u=User(clinic_id=clinic.id,doctor_id=None,email=email,full_name=body.full_name.strip(),password_hash=hash_password(body.password),role=UserRole.OWNER,is_active=True)
    db.add(u); db.commit(); db.refresh(u); return {"access_token":make_token(u),"user":u}

@app.post("/auth/login",response_model=TokenOut)
def auth_login(body:LoginIn,db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==body.email.strip().lower()))
    if not u or not u.is_active or not verify_password(body.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
    return {"access_token":make_token(u),"user":u}
@app.get("/auth/me",response_model=UserOut)
def auth_me(request:Request,db:Session=Depends(get_db)):
    u=db.get(User,int(request.state.user["sub"]))
    if not u or not u.is_active: raise HTTPException(401,"User unavailable")
    return u


def _validate_user_role(db:Session, clinic_id:int, role_text:str, doctor_id:int|None):
    try: role=UserRole(role_text.upper())
    except ValueError: raise HTTPException(400,"Role must be OWNER, SECRETARY or DOCTOR")
    if role==UserRole.DOCTOR:
        if not doctor_id: raise HTTPException(400,"Doctor role must be linked to a doctor")
        doctor=db.get(Doctor,doctor_id)
        if not doctor or doctor.clinic_id!=clinic_id: raise HTTPException(404,"Doctor not found in clinic")
    elif doctor_id is not None:
        raise HTTPException(400,"doctor_id is only valid for DOCTOR users")
    return role

@app.get("/users",response_model=list[UserOut])
def list_users(request:Request,db:Session=Depends(get_db)):
    if request.state.user["role"]!="OWNER": raise HTTPException(403,"OWNER role required")
    return db.scalars(select(User).where(User.clinic_id==int(request.state.user["clinic_id"])).order_by(User.full_name)).all()

@app.post("/users",response_model=UserOut)
def create_user(body:UserCreate,request:Request,db:Session=Depends(get_db)):
    if request.state.user["role"]!="OWNER": raise HTTPException(403,"OWNER role required")
    clinic_id=int(request.state.user["clinic_id"]); email=body.email.strip().lower()
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,"Email already exists")
    role=_validate_user_role(db,clinic_id,body.role,body.doctor_id)
    u=User(clinic_id=clinic_id,doctor_id=body.doctor_id,email=email,full_name=body.full_name.strip(),password_hash=hash_password(body.password),role=role,is_active=True)
    db.add(u); db.commit(); db.refresh(u); return u

@app.patch("/users/{user_id}",response_model=UserOut)
def update_user(user_id:int,body:UserUpdate,request:Request,db:Session=Depends(get_db)):
    if request.state.user["role"]!="OWNER": raise HTTPException(403,"OWNER role required")
    u=db.get(User,user_id)
    if not u or u.clinic_id!=int(request.state.user["clinic_id"]): raise HTTPException(404,"User not found")
    new_role=body.role.upper() if body.role else _role_value(u)
    new_doctor=body.doctor_id if body.role is not None or body.doctor_id is not None else u.doctor_id
    role=_validate_user_role(db,u.clinic_id,new_role,new_doctor)
    if body.is_active is False and u.id==int(request.state.user["sub"]): raise HTTPException(409,"You cannot deactivate your own account")
    if (_role_value(u)=="OWNER" and (role!=UserRole.OWNER or body.is_active is False)):
        other=db.scalar(select(func.count(User.id)).where(User.clinic_id==u.clinic_id,User.role==UserRole.OWNER,User.is_active==True,User.id!=u.id)) or 0
        if other==0: raise HTTPException(409,"At least one active OWNER is required")
    if body.full_name is not None: u.full_name=body.full_name.strip()
    u.role=role; u.doctor_id=new_doctor
    if body.is_active is not None: u.is_active=body.is_active
    if body.password: u.password_hash=hash_password(body.password)
    db.commit(); db.refresh(u); return u

@app.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(request: Request, limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    if request.state.user["role"] != "OWNER":
        raise HTTPException(403, "OWNER role required")
    clinic_id = int(request.state.user["clinic_id"])
    return db.scalars(
        select(AuditLog).where(AuditLog.clinic_id == clinic_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
    ).all()

@app.get("/health")
def health(): return {"status":"ok","version":"4.5.3-pilot.1"}

@app.post("/clinics", response_model=ClinicOut)
def create_clinic(body: ClinicCreate, request:Request, db: Session=Depends(get_db)):
    raise HTTPException(403,"Creating additional clinics is disabled in pilot mode")
@app.get("/clinics", response_model=list[ClinicOut])
def list_clinics(request:Request, db: Session=Depends(get_db)):
    return db.scalars(select(Clinic).where(Clinic.id==int(request.state.user["clinic_id"]))).all()

@app.patch("/clinics/{clinic_id}", response_model=ClinicOut)
def update_clinic(clinic_id:int, body:ClinicUpdate, db:Session=Depends(get_db)):
    obj=db.get(Clinic,clinic_id)
    if not obj: raise HTTPException(404,"Clinic not found")
    obj.name=body.name.strip(); obj.timezone=body.timezone.strip() or "Asia/Beirut"
    db.commit(); db.refresh(obj); return obj

@app.post("/doctors", response_model=DoctorOut)
def create_doctor(body: DoctorCreate, request:Request, db: Session=Depends(get_db)):
    if body.clinic_id!=int(request.state.user["clinic_id"]): raise HTTPException(403,"Clinic access denied")
    if not db.get(Clinic, body.clinic_id): raise HTTPException(404,"Clinic not found")
    obj=Doctor(**body.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@app.get("/doctors", response_model=list[DoctorOut])
def list_doctors(clinic_id:int, request:Request, db:Session=Depends(get_db)):
    stmt=select(Doctor).where(Doctor.clinic_id==clinic_id)
    if request.state.user["role"]=="DOCTOR":
        stmt=stmt.where(Doctor.id==request.state.user["doctor_id"])
    return db.scalars(stmt.order_by(Doctor.name)).all()

@app.patch("/doctors/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id:int, body:DoctorUpdate, db:Session=Depends(get_db)):
    obj=db.get(Doctor,doctor_id)
    if not obj: raise HTTPException(404,"Doctor not found")
    obj.name=body.name.strip(); obj.specialty=body.specialty.strip() if body.specialty else None
    db.commit(); db.refresh(obj); return obj

@app.post("/services", response_model=ServiceOut)
def create_service(body: ServiceCreate, request:Request, db: Session=Depends(get_db)):
    if body.clinic_id!=int(request.state.user["clinic_id"]): raise HTTPException(403,"Clinic access denied")
    if not db.get(Clinic, body.clinic_id): raise HTTPException(404,"Clinic not found")
    if body.duration_minutes <= 0: raise HTTPException(400,"Duration must be greater than zero")
    obj=Service(**body.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@app.get("/services", response_model=list[ServiceOut])
def list_services(clinic_id:int, db:Session=Depends(get_db)):
    return db.scalars(select(Service).where(Service.clinic_id==clinic_id).order_by(Service.name)).all()

@app.patch("/services/{service_id}", response_model=ServiceOut)
def update_service(service_id:int, body:ServiceUpdate, db:Session=Depends(get_db)):
    obj=db.get(Service,service_id)
    if not obj: raise HTTPException(404,"Service not found")
    if body.duration_minutes <= 0: raise HTTPException(400,"Duration must be greater than zero")
    obj.name=body.name.strip(); obj.duration_minutes=body.duration_minutes; obj.price=body.price
    db.commit(); db.refresh(obj); return obj

@app.post("/patients", response_model=PatientOut)
def create_patient(body: PatientCreate, request:Request, db: Session=Depends(get_db)):
    if body.clinic_id!=int(request.state.user["clinic_id"]): raise HTTPException(403,"Clinic access denied")
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
def add_schedule(doctor_id:int, body:ScheduleCreate, request:Request, db:Session=Depends(get_db)):
    if body.clinic_id!=int(request.state.user["clinic_id"]): raise HTTPException(403,"Clinic access denied")
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
def create_appointment(body:AppointmentCreate, request:Request, db:Session=Depends(get_db)):
    if body.clinic_id!=int(request.state.user["clinic_id"]): raise HTTPException(403,"Clinic access denied")
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
def add_waiting_list(body: WaitingListCreate, request:Request, db:Session=Depends(get_db)):
    if body.clinic_id!=int(request.state.user["clinic_id"]): raise HTTPException(403,"Clinic access denied")
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
