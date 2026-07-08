import asyncio
import secrets
from datetime import datetime, timedelta

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, Response, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import SessionLocal, get_db
from app.models import Email, Lead, Task, User
from app.schemas import (
    AnalyticsResponse,
    BulkImportResponse,
    EmailGenerateRequest,
    EmailRead,
    LeadEnrichmentWebhookRequest,
    LeadCaptureRequest,
    LeadCreate,
    LeadRead,
    LeadScoreWebhookRequest,
    LeadUpdate,
    LoginRequest,
    N8nCreateTaskRequest,
    N8nUpdateLeadRequest,
    ReportingResponse,
    TaskCreate,
    TaskRead,
    TaskWebhookResponse,
    TaskUpdate,
    TokenResponse,
    UserCreate,
    UserRead,
    WebhookLeadResponse,
)
from app.services import build_task_description
from services.assignment_service import assign_lead
from services.auth_service import create_access_token, get_current_user, hash_password, require_roles, verify_password
from services.import_service import import_leads_from_csv
from services.reporting_service import build_summary, send_summary
from services.ai_service import (
    AIRateLimitError,
    enrich_lead_with_ai,
    generate_personalized_email,
    score_lead_with_ai,
)
from services.websocket_manager import manager


app = FastAPI(title="AI CRM API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMPORT_JOBS: dict[str, dict] = {}


@app.on_event("startup")
async def start_reporting_scheduler():
    async def scheduled_report_loop():
        while True:
            await asyncio.sleep(max(1, app.state.reporting_interval_seconds))
            db = SessionLocal()
            try:
                summary = build_summary(db)
                await send_summary(summary)
            finally:
                db.close()

    app.state.reporting_interval_seconds = settings.reporting_interval_minutes * 60
    app.state.reporting_task = asyncio.create_task(scheduled_report_loop())


def get_lead_or_404(db: Session, lead_id: int) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def commit_or_conflict(db: Session, conflict_message: str):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_message) from exc


def lead_to_payload(lead: Lead, extra_context: dict | None = None) -> dict:
    payload = {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "source": lead.source,
        "status": lead.status,
        "lead_score": lead.lead_score,
        "category": lead.category,
        "ai_metadata": lead.ai_metadata or {},
    }
    if extra_context:
        payload.update(extra_context)
    return payload


def merge_ai_metadata(lead: Lead, key: str, value: dict) -> None:
    lead.ai_metadata = {**(lead.ai_metadata or {}), key: value}


def run_ai_operation(operation):
    try:
        return operation()
    except AIRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


def priority_from_score(score: int) -> tuple[str, datetime]:
    if score >= 75:
        return "high", datetime.utcnow() + timedelta(hours=4)
    if score >= 45:
        return "medium", datetime.utcnow() + timedelta(days=1)
    return "low", datetime.utcnow() + timedelta(days=3)


def task_description_for_priority(lead: Lead, priority: str, context: dict) -> str:
    action = context.get("next_action") or "follow up"
    return f"[{priority.upper()}] {action} with {lead.name}"


async def broadcast_lead_score(lead: Lead) -> None:
    await manager.broadcast(
        {
            "type": "lead_score_updated",
            "lead_id": lead.id,
            "lead_score": lead.lead_score,
            "category": lead.category,
            "assigned_to": lead.assigned_to,
            "updated_at": datetime.utcnow().isoformat(),
        }
    )


async def process_import_job(job_id: str, csv_text: str) -> None:
    IMPORT_JOBS[job_id]["status"] = "processing"
    db = SessionLocal()
    try:
        result = import_leads_from_csv(csv_text, db)
        IMPORT_JOBS[job_id] = {"status": "completed", "result": result}
        await manager.broadcast({"type": "bulk_import_completed", "job_id": job_id, "result": result})
    except Exception as exc:
        IMPORT_JOBS[job_id] = {"status": "failed", "error": str(exc)}
        await manager.broadcast({"type": "bulk_import_failed", "job_id": job_id, "error": str(exc)})
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.websocket("/ws/leads")
async def lead_updates_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hash_password(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email, User.is_active.is_(True)).first()
    if user is None or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return {"access_token": create_access_token(user.email, user.role), "user": user}


@app.get("/auth/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(lead: LeadCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    lead_data = lead.model_dump()
    provided_metadata = lead_data.pop("ai_metadata", {}) or {}
    if lead_data["lead_score"] is None:
        ai_score = run_ai_operation(lambda: score_lead_with_ai({**lead_data, **provided_metadata}))
        lead_data["lead_score"] = ai_score["score"]
        lead_data["category"] = ai_score["category"]
        provided_metadata = {**provided_metadata, "score": ai_score}
    elif lead_data.get("category") is None:
        ai_score = run_ai_operation(lambda: score_lead_with_ai({**lead_data, **provided_metadata}))
        lead_data["category"] = ai_score["category"]
        provided_metadata = {**provided_metadata, "score": ai_score}

    db_lead = Lead(**lead_data, ai_metadata=provided_metadata)
    db.add(db_lead)
    db.flush()
    assign_lead(db_lead)
    commit_or_conflict(db, "A lead with this email already exists")
    db.refresh(db_lead)
    background_tasks.add_task(broadcast_lead_score, db_lead)
    return db_lead


@app.post("/leads/capture", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def capture_lead(request: LeadCaptureRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    payload = request.model_dump()
    context = payload.pop("context", {}) or {}
    ai_score = run_ai_operation(lambda: score_lead_with_ai({**payload, **context}))
    lead = Lead(
        name=payload["name"],
        email=payload["email"],
        company=payload.get("company"),
        source=payload.get("source"),
        status="captured",
        lead_score=ai_score["score"],
        category=ai_score["category"],
        ai_metadata={"capture": payload, "score": ai_score, "context": context},
    )
    db.add(lead)
    db.flush()
    assign_lead(lead)
    commit_or_conflict(db, "A lead with this email already exists")
    db.refresh(lead)
    background_tasks.add_task(broadcast_lead_score, lead)
    return lead


@app.post("/leads/import", response_model=BulkImportResponse)
async def import_leads_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("admin", "manager")),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file required")
    csv_text = (await file.read()).decode("utf-8-sig")
    job_id = secrets.token_urlsafe(12)
    IMPORT_JOBS[job_id] = {"status": "queued", "user": current_user.email, "filename": file.filename}
    background_tasks.add_task(process_import_job, job_id, csv_text)
    return {"queued": True, "filename": file.filename, "job_id": job_id, "result": IMPORT_JOBS[job_id]}


@app.get("/leads/import/{job_id}")
def get_import_job(job_id: str, current_user: User = Depends(require_roles("admin", "manager"))):
    job = IMPORT_JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return job


@app.get("/leads", response_model=list[LeadRead])
def list_leads(
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    score: int | None = Query(default=None, ge=0, le=100),
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_score cannot be greater than max_score",
        )

    query = db.query(models.Lead)
    if status_filter is not None:
        query = query.filter(models.Lead.status == status_filter)
    if category is not None:
        query = query.filter(models.Lead.category == category)
    if score is not None:
        query = query.filter(models.Lead.lead_score == score)
    if min_score is not None:
        query = query.filter(models.Lead.lead_score >= min_score)
    if max_score is not None:
        query = query.filter(models.Lead.lead_score <= max_score)

    return query.order_by(models.Lead.created_at.desc()).all()


@app.get("/leads/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    return get_lead_or_404(db, lead_id)


@app.put("/leads/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: int, lead_update: LeadUpdate, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, lead_id)
    update_data = lead_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    assign_lead(lead)
    commit_or_conflict(db, "A lead with this email already exists")
    db.refresh(lead)
    return lead


@app.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, lead_id)
    db.delete(lead)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, task.lead_id)
    task_data = task.model_dump()
    if task_data["description"] is None:
        task_data["description"] = build_task_description(lead)

    db_task = Task(**task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    lead_id: int | None = Query(default=None, gt=0),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if lead_id is not None:
        query = query.filter(Task.lead_id == lead_id)
    if status_filter is not None:
        query = query.filter(Task.status == status_filter)
    return query.order_by(Task.id.desc()).all()


@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@app.post("/emails/generate", response_model=EmailRead, status_code=status.HTTP_201_CREATED)
def generate_email(request: EmailGenerateRequest, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, request.lead_id)
    ai_email = run_ai_operation(
        lambda: generate_personalized_email(
            lead_to_payload(lead, request.context),
            purpose=request.purpose,
            tone=request.tone,
        )
    )
    subject = request.subject or ai_email["subject"]
    tracking_token = secrets.token_urlsafe(24)
    tracking_metadata = {
        **ai_email,
        "open_pixel_url": f"{settings.public_api_base_url}/emails/track/open/{tracking_token}.png",
        "click_tracking_base_url": f"{settings.public_api_base_url}/emails/track/click/{tracking_token}",
    }
    db_email = Email(lead_id=lead.id, subject=subject, body=ai_email["body"], tracking_token=tracking_token)
    merge_ai_metadata(lead, "last_generated_email", tracking_metadata)
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email


@app.get("/emails", response_model=list[EmailRead])
def list_emails(lead_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db)):
    query = db.query(Email)
    if lead_id is not None:
        query = query.filter(Email.lead_id == lead_id)
    return query.order_by(Email.id.desc()).all()


@app.post("/webhooks/lead-enrichment", response_model=WebhookLeadResponse)
def webhook_lead_enrichment(request: LeadEnrichmentWebhookRequest, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, request.lead_id)
    ai_result = run_ai_operation(lambda: enrich_lead_with_ai(lead_to_payload(lead, request.context)))
    merge_ai_metadata(lead, "enrichment", ai_result)
    db.commit()
    db.refresh(lead)
    return {"lead": lead, "ai_result": ai_result}


@app.post("/webhooks/lead-score", response_model=WebhookLeadResponse)
def webhook_lead_score(request: LeadScoreWebhookRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, request.lead_id)
    scoring_context = request.model_dump(exclude={"lead_id"})
    context = scoring_context.pop("context", {}) or {}
    ai_result = run_ai_operation(lambda: score_lead_with_ai(lead_to_payload(lead, {**scoring_context, **context})))
    lead.lead_score = ai_result["score"]
    lead.category = ai_result["category"]
    merge_ai_metadata(lead, "score", ai_result)
    assign_lead(lead)
    db.commit()
    db.refresh(lead)
    background_tasks.add_task(broadcast_lead_score, lead)
    return {"lead": lead, "ai_result": ai_result}


@app.post("/webhooks/generate-email", response_model=EmailRead, status_code=status.HTTP_201_CREATED)
def webhook_generate_email(request: EmailGenerateRequest, db: Session = Depends(get_db)):
    return generate_email(request, db)


@app.post("/webhooks/update-lead", response_model=WebhookLeadResponse)
def webhook_update_lead(request: N8nUpdateLeadRequest, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, request.lead_id)
    update_data = request.model_dump(exclude={"lead_id"}, exclude_unset=True)

    for field in ("status", "lead_score", "category", "company", "source", "assigned_to"):
        if field in update_data and update_data[field] is not None:
            setattr(lead, field, update_data[field])

    workflow_payload = {
        "workflow_run_id": request.workflow_run_id,
        "ai_metadata": request.ai_metadata,
        "enrichment": request.enrichment,
        "scoring": request.scoring,
        "email": request.email,
        "error": request.error,
    }
    merge_ai_metadata(lead, "n8n", workflow_payload)
    if lead.assigned_to is None:
        assign_lead(lead)
    commit_or_conflict(db, "A lead with this email already exists")
    db.refresh(lead)
    return {"lead": lead, "ai_result": workflow_payload}


@app.post("/webhooks/create-task", response_model=TaskWebhookResponse, status_code=status.HTTP_201_CREATED)
def webhook_create_task(request: N8nCreateTaskRequest, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, request.lead_id)
    priority, default_due_date = priority_from_score(lead.lead_score)
    priority = request.priority or priority
    task_context = request.context or {}
    description = request.description or task_description_for_priority(lead, priority, task_context)
    due_date = request.due_date or default_due_date

    db_task = Task(
        lead_id=lead.id,
        description=description,
        due_date=due_date,
        status=request.status,
    )
    merge_ai_metadata(
        lead,
        "last_task_assignment",
        {"priority": priority, "due_date": due_date.isoformat(), "context": task_context},
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {
        "task": db_task,
        "priority": priority,
        "ai_result": {"priority": priority, "context": task_context},
    }


@app.get("/emails/track/open/{token}.png")
def track_email_open(token: str, db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.tracking_token == token).first()
    if email:
        email.open_count += 1
        email.opened_at = datetime.utcnow()
        db.commit()
    pixel = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
    return Response(content=pixel, media_type="image/gif")


@app.get("/emails/track/click/{token}")
def track_email_click(token: str, url: str, db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.tracking_token == token).first()
    if email:
        email.click_count += 1
        email.clicked_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url=url)


@app.get("/analytics/overview", response_model=AnalyticsResponse)
def analytics_overview(current_user: User = Depends(require_roles("admin", "manager", "sales")), db: Session = Depends(get_db)):
    leads = db.query(Lead).all()
    emails = db.query(Email).all()
    total = len(leads)
    statuses = ["captured", "new", "contacted", "qualified", "converted"]
    funnel = [{"stage": stage, "count": len([lead for lead in leads if lead.status == stage])} for stage in statuses]
    sources = sorted({lead.source or "unknown" for lead in leads})
    source_effectiveness = [
        {
            "source": source,
            "leads": len([lead for lead in leads if (lead.source or "unknown") == source]),
            "avg_score": round(
                sum(lead.lead_score for lead in leads if (lead.source or "unknown") == source)
                / max(1, len([lead for lead in leads if (lead.source or "unknown") == source])),
                2,
            ),
        }
        for source in sources
    ]
    ai_accuracy = [
        {"metric": "scored", "value": len([lead for lead in leads if (lead.ai_metadata or {}).get("score")])},
        {"metric": "enriched", "value": len([lead for lead in leads if (lead.ai_metadata or {}).get("enrichment")])},
        {"metric": "email opens", "value": sum(email.open_count for email in emails)},
        {"metric": "email clicks", "value": sum(email.click_count for email in emails)},
    ]
    routing = [
        {"assignee": assignee or "unassigned", "count": len([lead for lead in leads if lead.assigned_to == assignee])}
        for assignee in sorted({lead.assigned_to for lead in leads})
    ]
    if total == 0:
        funnel = [{"stage": stage, "count": 0} for stage in statuses]
    return {"funnel": funnel, "source_effectiveness": source_effectiveness, "ai_accuracy": ai_accuracy, "routing": routing}


@app.post("/reports/send-summary", response_model=ReportingResponse)
async def send_report_summary(current_user: User = Depends(require_roles("admin", "manager")), db: Session = Depends(get_db)):
    summary = build_summary(db)
    result = await send_summary(summary)
    return {"sent": bool(result.get("sent")), "result": result}
