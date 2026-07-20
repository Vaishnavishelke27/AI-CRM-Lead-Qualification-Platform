from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LeadBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    company: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=100)
    status: str = Field(default="new", min_length=1, max_length=50)
    lead_score: int = Field(default=0, ge=0, le=100)
    category: str | None = Field(default=None, max_length=100)
    assigned_to: str | None = Field(default=None, max_length=255)
    ai_metadata: dict = Field(default_factory=dict)


class LeadCreate(LeadBase):
    lead_score: int | None = Field(default=None, ge=0, le=100)


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    company: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    lead_score: int | None = Field(default=None, ge=0, le=100)
    category: str | None = Field(default=None, max_length=100)
    assigned_to: str | None = Field(default=None, max_length=255)
    ai_metadata: dict | None = None


class LeadCaptureRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    company: str | None = Field(default=None, max_length=255)
    source: str = Field(default="landing_page", min_length=1, max_length=100)
    form_id: str | None = Field(default=None, max_length=255)
    page_url: str | None = Field(default=None, max_length=500)
    engagement_level: str | None = Field(default=None, max_length=100)
    context: dict = Field(default_factory=dict)


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TaskCreate(BaseModel):
    lead_id: int = Field(..., gt=0)
    description: str | None = Field(default=None, min_length=1)
    due_date: datetime | None = None
    status: str = Field(default="open", min_length=1, max_length=50)


class TaskUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1)
    due_date: datetime | None = None
    status: str | None = Field(default=None, min_length=1, max_length=50)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    description: str
    due_date: datetime | None
    status: str

class EmailGenerateRequest(BaseModel):
    lead_id: int = Field(..., gt=0)
    purpose: str = Field(default="follow_up", min_length=1, max_length=100)
    tone: str = Field(default="professional", min_length=1, max_length=100)
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    context: dict = Field(default_factory=dict)


class LeadEnrichmentWebhookRequest(BaseModel):
    lead_id: int = Field(..., gt=0)
    context: dict = Field(default_factory=dict)


class LeadScoreWebhookRequest(BaseModel):
    lead_id: int = Field(..., gt=0)
    company_size: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    engagement_level: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=100)
    context: dict = Field(default_factory=dict)


class WebhookLeadResponse(BaseModel):
    lead: LeadRead
    ai_result: dict


class N8nUpdateLeadRequest(BaseModel):
    lead_id: int = Field(..., gt=0)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    lead_score: int | None = Field(default=None, ge=0, le=100)
    category: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=100)
    assigned_to: str | None = Field(default=None, max_length=255)
    ai_metadata: dict = Field(default_factory=dict)
    enrichment: dict = Field(default_factory=dict)
    scoring: dict = Field(default_factory=dict)
    email: dict = Field(default_factory=dict)
    workflow_run_id: str | None = Field(default=None, max_length=255)
    error: dict | None = None


class N8nCreateTaskRequest(BaseModel):
    lead_id: int = Field(..., gt=0)
    description: str | None = Field(default=None, min_length=1)
    due_date: datetime | None = None
    status: str = Field(default="open", min_length=1, max_length=50)
    priority: str | None = Field(default=None, max_length=50)
    context: dict = Field(default_factory=dict)


class TaskWebhookResponse(BaseModel):
    task: TaskRead
    priority: str
    ai_result: dict


class EmailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    subject: str
    body: str
    sent_at: datetime | None
    tracking_token: str | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    open_count: int = 0
    click_count: int = 0

class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class BulkImportResponse(BaseModel):
    queued: bool
    filename: str
    job_id: str | None = None
    result: dict


class AnalyticsResponse(BaseModel):
    funnel: list[dict]
    source_effectiveness: list[dict]
    ai_accuracy: list[dict]
    routing: list[dict]


class ReportingResponse(BaseModel):
    sent: bool
    result: dict
