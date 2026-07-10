# Detailed Project Report: AI CRM

## 1. Project Overview

The project is named **AI CRM**. It is a full-stack Customer Relationship Management application built for managing leads, sales follow-up tasks, generated outreach emails, analytics, and AI-assisted lead processing.

The project is implemented as a web application with two main parts:

- A **React frontend** located in `frontend/`
- A **FastAPI backend** located in `backend/`

The backend exposes REST API endpoints and a WebSocket endpoint. The frontend consumes those endpoints and presents a CRM dashboard in the browser. The application stores CRM data in a relational database using SQLAlchemy models and supports PostgreSQL through Docker and environment configuration.

The project focuses on these main CRM capabilities:

- Creating, viewing, updating, filtering, sorting, and deleting leads
- Automatically scoring leads using AI or deterministic fallback logic
- Categorizing leads as Hot, Warm, or Cold
- Assigning leads to sales owners based on category
- Creating and updating follow-up tasks
- Generating personalized email drafts for selected leads
- Tracking generated email opens and clicks through tracking URLs
- Displaying dashboard metrics and analytics
- Authenticating users with JWT tokens
- Restricting selected operations by user role
- Importing leads from CSV files
- Supporting n8n-style webhook workflows
- Broadcasting lead updates over WebSockets
- Running the stack with Docker Compose

This report is strictly based on the files present in this project.

## 2. Repository Structure

The root folder contains the main project configuration and documentation:

```text
AI + CRM/
  .env.example
  .gitignore
  docker-compose.yml
  PROJECT_DETAILED_REPORT.md
  README.md
  render.yaml
  backend/
  frontend/
```

The important backend files are:

```text
backend/
  Dockerfile
  alembic.ini
  models.py
  requirements.txt
  app/
    __init__.py
    config.py
    database.py
    main.py
    models.py
    schemas.py
    services.py
  services/
    __init__.py
    ai_service.py
    assignment_service.py
    auth_service.py
    import_service.py
    reporting_service.py
    websocket_manager.py
  alembic/
    env.py
    script.py.mako
    versions/
      20260708_0001_initial_crm_schema.py
      20260708_0002_add_lead_metadata.py
      20260708_0003_growth_features.py
  workflows/
    main_lead_processing.workflow.json
    lead_enrichment_subworkflow.workflow.json
    email_personalization_subworkflow.workflow.json
    task_priority_subworkflow.workflow.json
    error_retry_handler.workflow.json
```

The important frontend files are:

```text
frontend/
  Dockerfile
  index.html
  package.json
  package-lock.json
  src/
    main.jsx
    styles.css
    api/
      client.js
    context/
      CRMContext.jsx
    components/
      AnalyticsDashboard.jsx
      AuthPanel.jsx
      EmailComposer.jsx
      LeadDashboard.jsx
      LeadDetail.jsx
      LeadForm.jsx
      LeadTable.jsx
      TaskManagement.jsx
```

## 3. Technology Stack

### 3.1 Frontend Stack

The frontend is built with:

- React
- React DOM
- Vite
- JavaScript modules
- CSS
- lucide-react
- Recharts

The `frontend/package.json` file defines the frontend package as `ai-crm-frontend`. It includes the scripts:

```text
npm run dev
npm run build
npm run preview
```

Vite is used as the development server and production bundler. React is used to build the user interface. lucide-react provides icons for navigation, buttons, KPI cards, and action controls. Recharts is used for analytics charts.

### 3.2 Backend Stack

The backend is built with:

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- Alembic
- python-jose
- passlib
- bcrypt
- OpenAI SDK
- Anthropic SDK
- httpx
- python-multipart
- email-validator
- psycopg2-binary

FastAPI defines the API routes. Uvicorn runs the ASGI server. SQLAlchemy defines models and database sessions. Pydantic validates API request and response schemas. Alembic stores database migration files. python-jose creates and verifies JWT tokens. passlib and bcrypt handle password hashing. The OpenAI and Anthropic SDKs are used when AI provider keys are configured. httpx is currently used in the reporting service placeholder.

### 3.3 Database Stack

The project is designed around SQLAlchemy and a relational database.

In the current code, the default `DATABASE_URL` in `backend/app/config.py` is:

```text
postgresql://postgres:postgres@127.0.0.1:5433/ai_crm
```

The Docker Compose file maps the PostgreSQL container from container port `5432` to host port `5433`:

```text
5433:5432
```

Inside Docker, the backend receives:

```text
postgresql://postgres:postgres@postgres:5432/ai_crm
```

The database layer also contains SQLite-specific compatibility logic. If `DATABASE_URL` starts with `sqlite`, the backend uses SQLite connection arguments and performs simple column-add checks during startup. However, SQLite is not the default value in the current `config.py`; PostgreSQL on port `5433` is the current default.

## 4. High-Level Architecture

The project follows a separated frontend-backend architecture:

```text
Browser
  |
  v
React + Vite frontend
  |
  | HTTP fetch requests
  | WebSocket connection
  v
FastAPI backend
  |
  v
SQLAlchemy ORM
  |
  v
PostgreSQL database
```

The frontend runs on:

```text
http://localhost:5173
```

The backend runs on:

```text
http://localhost:8000
```

The database is PostgreSQL when using Docker Compose. The host port is:

```text
localhost:5433
```

This separation allows the frontend to focus on interface behavior while the backend handles data validation, persistence, authentication, AI logic, reporting, imports, webhooks, and WebSocket updates.

## 5. Backend Application Entry Point

The backend starts from:

```text
backend/app/main.py
```

This file creates the FastAPI app:

```python
app = FastAPI(title="AI CRM API", version="0.2.0")
```

The backend also adds CORS middleware so the React frontend can call the API from a different origin:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The backend startup event performs two actions:

- Calls `initialize_database()`
- Starts a scheduled reporting loop

The reporting loop sleeps for `REPORTING_INTERVAL_MINUTES * 60` seconds, builds a summary, and calls the reporting sender. The sender is currently a placeholder because no real email provider endpoint is configured.

## 6. Configuration

Configuration is defined in:

```text
backend/app/config.py
```

The `Settings` class reads environment variables with default values. The main settings are:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `CLAUDE_API_KEY`
- `AI_PROVIDER`
- `OPENAI_MODEL`
- `CLAUDE_MODEL`
- `AI_CACHE_TTL_SECONDS`
- `AI_RATE_LIMIT_PER_MINUTE`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REPORTING_INTERVAL_MINUTES`
- `REPORTING_EMAIL_TO`
- `FRONTEND_ORIGINS`
- `PUBLIC_API_BASE_URL`

The `.env.example` file lists expected environment variables for local or deployed configuration. It also includes workflow-related values:

- `CRM_API_BASE_URL`
- `COMPANY_SCRAPE_URL`
- `DECISION_MAKER_LOOKUP_URL`

These values support the n8n workflow files included in `backend/workflows/`.

## 7. Database Layer

The database connection is defined in:

```text
backend/app/database.py
```

This file creates:

- SQLAlchemy engine
- Session factory
- Declarative base class
- `initialize_database()`
- `get_db()` dependency

The engine is created using the configured database URL:

```python
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
```

The `pool_pre_ping=True` option helps detect stale database connections before using them.

The `get_db()` function is a FastAPI dependency. API routes use it to receive a database session:

```python
db: Session = Depends(get_db)
```

The session is yielded to the route and closed afterward.

The `initialize_database()` function calls:

```python
Base.metadata.create_all(bind=engine)
```

This creates missing tables from the SQLAlchemy models. For SQLite only, it also checks existing columns and adds missing compatibility columns for lead metadata, assignment, and email tracking.

## 8. Database Models

The main database models are defined in:

```text
backend/app/models.py
```

There is also a compatibility re-export file:

```text
backend/models.py
```

That file imports `Email`, `Lead`, `Task`, and `User` from `app.models`.

The project defines four main tables:

- `leads`
- `tasks`
- `emails`
- `users`

### 8.1 Lead Model

The `Lead` model represents a possible customer.

Important fields:

- `id`
- `name`
- `email`
- `company`
- `source`
- `status`
- `lead_score`
- `category`
- `assigned_to`
- `ai_metadata`
- `created_at`

The table includes a score constraint:

```text
lead_score >= 0 AND lead_score <= 100
```

The `email` field is unique and indexed. This prevents duplicate lead emails.

The `ai_metadata` Python attribute is stored in the database column named `metadata`. It stores JSON data such as scoring results, enrichment results, assignment information, generated email metadata, n8n workflow payloads, and task assignment context.

The `Lead` model has relationships to:

- `tasks`
- `emails`

Both relationships use `cascade="all, delete-orphan"`, so deleting a lead also deletes its related tasks and emails through the ORM relationship.

### 8.2 Task Model

The `Task` model represents a follow-up action linked to a lead.

Important fields:

- `id`
- `lead_id`
- `description`
- `due_date`
- `status`

The `lead_id` field references:

```text
leads.id
```

The foreign key uses `ondelete="CASCADE"`. The default task status is:

```text
open
```

### 8.3 Email Model

The `Email` model stores generated email drafts and tracking data.

Important fields:

- `id`
- `lead_id`
- `subject`
- `body`
- `sent_at`
- `tracking_token`
- `opened_at`
- `clicked_at`
- `open_count`
- `click_count`

The email belongs to a lead through `lead_id`. The `tracking_token` is unique and indexed. It is used by the tracking endpoints for open and click tracking.

The code generates email records, but the frontend sends actual email content through the user's local mail client using a `mailto:` link. The backend does not currently send generated emails through an email provider.

### 8.4 User Model

The `User` model stores login accounts.

Important fields:

- `id`
- `email`
- `full_name`
- `hashed_password`
- `role`
- `is_active`
- `created_at`

The allowed roles are enforced by the `UserCreate` schema:

```text
admin
manager
sales
```

The default role is:

```text
sales
```

## 9. Pydantic Schemas

API schemas are defined in:

```text
backend/app/schemas.py
```

These schemas validate request bodies and shape API responses.

Important lead schemas:

- `LeadBase`
- `LeadCreate`
- `LeadUpdate`
- `LeadCaptureRequest`
- `LeadRead`

Important task schemas:

- `TaskCreate`
- `TaskUpdate`
- `TaskRead`
- `N8nCreateTaskRequest`
- `TaskWebhookResponse`

Important email schemas:

- `EmailGenerateRequest`
- `EmailRead`

Important authentication schemas:

- `UserCreate`
- `UserRead`
- `LoginRequest`
- `TokenResponse`

Important webhook and analytics schemas:

- `LeadEnrichmentWebhookRequest`
- `LeadScoreWebhookRequest`
- `WebhookLeadResponse`
- `N8nUpdateLeadRequest`
- `BulkImportResponse`
- `AnalyticsResponse`
- `ReportingResponse`

The schemas enforce rules such as:

- Lead score must be between 0 and 100
- Email fields must be valid email addresses
- Required names must not be empty
- User passwords must be at least 8 characters
- User role must be `admin`, `manager`, or `sales`
- IDs in request bodies must be greater than zero

This validation protects the backend from invalid input before database operations run.

## 10. Authentication and Authorization

Authentication logic is implemented in:

```text
backend/services/auth_service.py
```

The project uses:

- Password hashing
- JWT access tokens
- OAuth2 bearer token extraction
- Role-based authorization dependencies

### 10.1 Password Hashing

The project uses passlib with bcrypt:

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

During registration, the backend stores a hashed password instead of the plain password:

```python
hashed_password=hash_password(user.password)
```

During login, the backend verifies the submitted password against the stored hash:

```python
verify_password(request.password, user.hashed_password)
```

### 10.2 JWT Tokens

After successful login, the backend creates a JWT token containing:

- `sub`: user email
- `role`: user role
- `exp`: expiration time

The token is encoded using:

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`

The frontend stores the token in `localStorage` under:

```text
ai_crm_token
```

Future API calls include:

```text
Authorization: Bearer <token>
```

### 10.3 Current User Resolution

The `get_current_user()` dependency:

1. Reads the bearer token
2. Decodes the JWT
3. Extracts the email from `sub`
4. Looks up an active user in the database
5. Returns the user or raises an authentication error

### 10.4 Role-Based Access

The `require_roles()` function creates dependencies for protected routes.

Routes that require roles include:

- `POST /leads/import`: `admin` or `manager`
- `GET /leads/import/{job_id}`: `admin` or `manager`
- `GET /analytics/overview`: `admin`, `manager`, or `sales`
- `POST /reports/send-summary`: `admin` or `manager`

If a logged-in user does not have one of the required roles, the backend returns:

```text
403 Forbidden
```

## 11. AI Service

AI logic is implemented in:

```text
backend/services/ai_service.py
```

This service handles:

- AI provider selection
- OpenAI calls
- Claude calls
- JSON extraction from model responses
- Lead scoring
- Lead enrichment
- Personalized email generation
- Deterministic fallback logic
- In-memory TTL caching
- Sliding-window rate limiting

### 11.1 Supported Providers

The service can call OpenAI or Anthropic Claude.

OpenAI uses:

```text
OPENAI_API_KEY
OPENAI_MODEL
```

Claude uses:

```text
CLAUDE_API_KEY
CLAUDE_MODEL
```

Provider preference is controlled by:

```text
AI_PROVIDER
```

If `AI_PROVIDER` is `claude` and a Claude key is configured, Claude is used. Otherwise, OpenAI is used if an OpenAI key exists. If only a Claude key exists, Claude is used.

### 11.2 JSON-Only AI Responses

The AI prompts tell the provider to return only valid JSON. The service also includes `_extract_json()`, which attempts to parse a response as JSON. If the whole response is not valid JSON, it searches for a JSON object inside the text.

### 11.3 AI Cache

The project uses an in-memory TTL cache:

```python
cache = InMemoryTTLCache(settings.ai_cache_ttl_seconds)
```

Cache keys are based on:

- operation name
- normalized JSON payload
- SHA-256 hash

If the same AI operation is requested with the same payload before the TTL expires, the cached value is reused and returned with:

```text
cached: true
```

The cache exists only in memory. It is lost when the backend process restarts.

### 11.4 AI Rate Limiting

The project uses a sliding-window rate limiter:

```python
rate_limiter = SlidingWindowRateLimiter(settings.ai_rate_limit_per_minute)
```

The limiter stores timestamps of recent AI calls. If the number of calls within the 60-second window reaches the configured maximum, it raises:

```text
AI API rate limit exceeded
```

The API wrapper converts this into:

```text
429 Too Many Requests
```

### 11.5 Lead Scoring

Lead scoring uses `score_lead_with_ai()`.

The AI prompt asks for:

- score from 0 to 100
- category as Hot, Warm, or Cold
- reasoning
- signals

If AI is unavailable or does not return a score, the deterministic fallback runs.

The fallback starts from a score of `20` and adjusts it using:

- company size
- industry
- engagement level
- source

Examples of positive scoring signals in the fallback:

- enterprise, 1000+, or large company size
- SaaS, software, technology, finance, or healthcare industry
- high engagement, demo requested, pricing page, or replied
- referral, demo, webinar, or partner source

The final score is clamped between 0 and 100.

Categories are assigned by score:

```text
75 to 100 = Hot
45 to 74  = Warm
0 to 44   = Cold
```

### 11.6 Lead Enrichment

Lead enrichment uses `enrich_lead_with_ai()`.

The AI prompt asks for:

- likely industry
- company size
- buyer persona
- pain points
- recommended next action
- confidence

If the provider is unavailable or returns an error, fallback enrichment is returned. The fallback stores a low-confidence result and recommends manual review and follow-up.

### 11.7 Personalized Email Generation

Email generation uses `generate_personalized_email()`.

The function receives:

- lead data
- purpose
- tone

It asks AI to return:

- subject
- body
- personalization notes

If AI is unavailable, it generates a deterministic fallback email using the lead name, company, and requested purpose.

## 12. Lead Assignment

Lead assignment is implemented in:

```text
backend/services/assignment_service.py
```

The project uses static sales routes:

```text
Hot  -> enterprise-ae@crm.local, senior-ae@crm.local
Warm -> growth-ae@crm.local, midmarket-ae@crm.local
Cold -> sdr@crm.local, nurture@crm.local
```

If the lead already has a category, that category is used. Otherwise, the category is inferred from score:

- score >= 75: Hot
- score >= 45: Warm
- otherwise: Cold

The selected assignee is chosen using the lead ID modulo the number of possible routes. The assignee is stored in:

```text
lead.assigned_to
```

The assignment result is also stored in lead metadata:

```text
ai_metadata.assignment
```

## 13. Task Description Helper

The file:

```text
backend/app/services.py
```

contains helper functions. The active helper used by `main.py` is:

```python
build_task_description(lead)
```

It returns a simple follow-up description such as:

```text
Follow up with Lead Name at Company
```

The same file also contains older helper functions for basic lead scoring and email content generation, but the main API currently uses the richer service modules for AI scoring and email generation.

## 14. CSV Import

CSV import logic is implemented in:

```text
backend/services/import_service.py
```

The API route is:

```text
POST /leads/import
```

This route requires an authenticated `admin` or `manager`.

The import route:

1. Accepts an uploaded file
2. Requires the filename to end with `.csv`
3. Reads the CSV as UTF-8 with BOM support
4. Creates a random job ID
5. Stores the job in the in-memory `IMPORT_JOBS` dictionary
6. Runs processing as a background task
7. Returns a queued response

The actual CSV processing:

1. Uses `csv.DictReader`
2. Requires `name` and `email`
3. Skips rows missing name or email
4. Skips duplicate email addresses
5. Reads optional fields such as company, source, status, company size, industry, and engagement level
6. Scores each lead using the AI scoring service
7. Creates the lead
8. Assigns the lead
9. Commits the imported records
10. Returns created and skipped counts

The job status can be checked through:

```text
GET /leads/import/{job_id}
```

Import jobs are stored in memory. They are not persisted in the database.

## 15. Reporting

Reporting logic is implemented in:

```text
backend/services/reporting_service.py
```

The summary builder calculates:

- generated timestamp
- total leads
- hot leads
- conversion rate
- open tasks

Converted leads are counted when status is one of:

```text
converted
won
customer
```

Open tasks are counted when task status is not:

```text
done
```

The report send route is:

```text
POST /reports/send-summary
```

This route requires `admin` or `manager`.

The `send_summary()` function currently behaves as follows:

- If `REPORTING_EMAIL_TO` is not configured, it returns `sent: false`
- If `REPORTING_EMAIL_TO` is configured, it still returns `sent: false` because the transactional email provider endpoint is not configured

Therefore, reporting summary generation is implemented, but real email delivery is still a placeholder.

## 16. WebSockets

WebSocket connection management is implemented in:

```text
backend/services/websocket_manager.py
```

The route is:

```text
WS /ws/leads
```

The connection manager keeps an in-memory list of active WebSocket connections. It can:

- accept a new connection
- remove a disconnected connection
- broadcast JSON messages to active clients

The backend broadcasts messages when:

- a lead score is updated
- a bulk import completes
- a bulk import fails

The frontend opens a WebSocket connection in `CRMContext.jsx`. When a message arrives, the frontend calls `refresh()` to reload CRM data.

## 17. API Routes

The backend routes are defined in:

```text
backend/app/main.py
```

### 17.1 Health Route

```text
GET /health
```

Returns:

```json
{"status":"ok"}
```

This route confirms that the backend process is running.

### 17.2 Authentication Routes

```text
POST /auth/register
POST /auth/login
GET /auth/me
```

`POST /auth/register` creates a new user if the email is not already registered.

`POST /auth/login` checks the email and password, then returns:

- access token
- token type
- user object

`GET /auth/me` returns the current authenticated user.

### 17.3 Lead Routes

```text
POST /leads
POST /leads/capture
POST /leads/import
GET /leads/import/{job_id}
GET /leads
GET /leads/{lead_id}
PUT /leads/{lead_id}
DELETE /leads/{lead_id}
```

`POST /leads` creates a manual lead. If no score is supplied, AI scoring runs. If a score is supplied but category is missing, AI scoring is still used to determine the category.

`POST /leads/capture` creates a captured lead from landing-page style data. It stores capture details and context in metadata.

`GET /leads` supports filters:

- `status`
- `category`
- `score`
- `min_score`
- `max_score`

If `min_score` is greater than `max_score`, the backend returns a bad request error.

`PUT /leads/{lead_id}` updates lead fields and re-runs assignment.

`DELETE /leads/{lead_id}` deletes a lead and returns `204 No Content`.

### 17.4 Task Routes

```text
POST /tasks
GET /tasks
PUT /tasks/{task_id}
```

`POST /tasks` creates a task. If no description is supplied, the backend builds a follow-up description from the lead.

`GET /tasks` supports optional filters:

- `lead_id`
- `status`

`PUT /tasks/{task_id}` updates task fields such as description, due date, and status.

### 17.5 Email Routes

```text
POST /emails/generate
GET /emails
GET /emails/track/open/{token}.png
GET /emails/track/click/{token}
```

`POST /emails/generate` generates email copy, creates a tracking token, stores the email, and stores tracking URLs in lead metadata.

`GET /emails` lists generated emails. It can filter by `lead_id`.

The open tracking route returns a one-pixel GIF and increments:

- `open_count`
- `opened_at`

The click tracking route requires a `url` query parameter. It increments:

- `click_count`
- `clicked_at`

Then it redirects to the supplied URL.

### 17.6 Webhook Routes

```text
POST /webhooks/lead-enrichment
POST /webhooks/lead-score
POST /webhooks/generate-email
POST /webhooks/update-lead
POST /webhooks/create-task
```

These routes support automation workflows such as the JSON workflows included under `backend/workflows/`.

`POST /webhooks/lead-enrichment` enriches a lead and stores the result in metadata.

`POST /webhooks/lead-score` scores a lead, updates score and category, reassigns the owner, and broadcasts a lead score update.

`POST /webhooks/generate-email` reuses the same logic as `POST /emails/generate`.

`POST /webhooks/update-lead` allows workflow callbacks to update lead fields and store workflow output in metadata.

`POST /webhooks/create-task` creates a task using lead-score priority logic. It assigns:

- high priority and due in 4 hours for score >= 75
- medium priority and due in 1 day for score >= 45
- low priority and due in 3 days otherwise

### 17.7 Analytics Route

```text
GET /analytics/overview
```

This route requires an authenticated user with role `admin`, `manager`, or `sales`.

It returns:

- funnel data
- source effectiveness data
- AI/email metrics
- sales routing data

The funnel stages are:

```text
captured
new
contacted
qualified
converted
```

Source effectiveness includes lead count and average score by source.

AI accuracy metrics include:

- scored leads
- enriched leads
- email opens
- email clicks

Routing metrics count leads by assignee.

## 18. Frontend Entry Point

The frontend starts from:

```text
frontend/src/main.jsx
```

It renders the React application into:

```text
document.getElementById("root")
```

The main layout is `AppShell`. It includes:

- sidebar
- top bar
- API status indicator
- refresh button
- error alert
- KPI dashboard
- analytics dashboard
- lead table
- lead detail panel
- authentication and operations panel
- manual lead form
- task management panel
- email composer

The frontend is a single-page dashboard. It does not use React Router in the current project.

## 19. Frontend API Client

API calls are centralized in:

```text
frontend/src/api/client.js
```

The API URL is:

```javascript
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
```

The WebSocket URL is derived from the API URL:

```javascript
export const WS_URL = API_URL.replace(/^http/, "ws");
```

The client stores the authentication token in memory and in local storage. The helper function `request()`:

1. Builds headers
2. Adds `Content-Type: application/json` except for `FormData`
3. Adds the authorization bearer token if available
4. Calls `fetch`
5. Handles `204 No Content`
6. Parses JSON
7. Throws an error when the response is not successful

The exported `api` object contains functions for:

- login
- register
- current user
- health
- lead listing
- lead creation
- lead update
- lead deletion
- AI enrichment
- AI scoring
- task listing
- task creation
- task update
- email listing
- email generation
- analytics
- lead import
- report sending

One important implementation detail is that the frontend's `createTask()` function calls:

```text
POST /webhooks/create-task
```

instead of:

```text
POST /tasks
```

This means frontend-created follow-up tasks use the priority-aware webhook task route.

## 20. Frontend State Management

Global CRM state is implemented in:

```text
frontend/src/context/CRMContext.jsx
```

The context stores:

- API health status
- leads
- tasks
- emails
- analytics
- logged-in user
- selected lead ID
- loading state
- error message

The `refresh()` function loads data from:

- `/health`
- `/leads`
- `/tasks`
- `/emails`
- `/analytics/overview`

Analytics loading is allowed to fail silently because analytics require authentication. If analytics cannot be loaded, the frontend stores `null` and shows a login message in the analytics panel.

The context also:

- loads the current user through `/auth/me`
- opens a WebSocket to `/ws/leads`
- refreshes data when a WebSocket message arrives
- exposes action methods to components

## 21. Frontend Components

### 21.1 LeadDashboard

File:

```text
frontend/src/components/LeadDashboard.jsx
```

This component displays KPI cards:

- Total leads
- Hot leads
- Conversion rate
- Open tasks

It calculates these values from frontend state. Hot leads are counted when category is Hot or score is at least 75. Converted leads are counted when status is converted, won, or customer. Open tasks are tasks whose status is not done.

### 21.2 AnalyticsDashboard

File:

```text
frontend/src/components/AnalyticsDashboard.jsx
```

This component displays charts using Recharts.

It shows:

- Lead conversion funnel
- Source effectiveness
- AI accuracy metrics
- Sales routing

If analytics are not available, it shows a panel asking the user to log in to view CRM analytics.

### 21.3 LeadTable

File:

```text
frontend/src/components/LeadTable.jsx
```

This component displays leads in a table-like layout.

It supports:

- Text search across name, company, and email
- Category filter
- Status filter
- Sorting by table columns
- Lead selection
- AI refresh action
- Lead deletion

The AI refresh action runs enrichment first and scoring second through the context methods.

### 21.4 LeadDetail

File:

```text
frontend/src/components/LeadDetail.jsx
```

This component displays the selected lead.

It shows:

- lead name
- email
- company
- status
- owner
- score
- category
- created date
- AI metadata
- related task timeline
- related generated email history

It also includes a button to refresh AI enrichment and score for the selected lead.

### 21.5 LeadForm

File:

```text
frontend/src/components/LeadForm.jsx
```

This component creates manual leads.

The form includes:

- name
- email
- company
- source
- status
- score
- category

Frontend validation checks:

- name is required
- email must match a basic email pattern
- score must be between 0 and 100

If the score is blank, the backend runs AI scoring.

### 21.6 AuthPanel

File:

```text
frontend/src/components/AuthPanel.jsx
```

This component handles login and operational actions.

When no user is logged in, it shows:

- email input
- password input
- sign-in button

When a user is logged in, it shows:

- import CSV control
- send summary button
- sign-out button

The component does not currently include a registration form, even though the API client supports registration.

### 21.7 TaskManagement

File:

```text
frontend/src/components/TaskManagement.jsx
```

This component lists tasks sorted by lead score priority and due date.

Priority is calculated from the related lead score:

- score >= 75: high
- score >= 45: medium
- otherwise: low

The component allows:

- creating a follow-up task for the selected lead
- marking a task open
- marking a task done

### 21.8 EmailComposer

File:

```text
frontend/src/components/EmailComposer.jsx
```

This component generates and prepares email drafts.

It uses three templates:

- Initial outreach
- Book demo
- Nurture follow-up

The order of suggested templates changes according to selected lead score:

- Hot leads prioritize book demo
- Warm leads prioritize initial outreach
- Cold leads prioritize nurture follow-up

The generate button calls the backend email generation route. The send button opens a `mailto:` link with the selected lead email, generated subject, and generated body.

## 22. Main Data Flows

### 22.1 Manual Lead Creation Flow

```text
User fills LeadForm
  |
  v
Frontend validates basic fields
  |
  v
Frontend calls POST /leads
  |
  v
Backend validates LeadCreate schema
  |
  v
If score is blank, backend runs AI or fallback scoring
  |
  v
Backend creates Lead model
  |
  v
Backend flushes to get lead ID
  |
  v
Assignment service assigns owner
  |
  v
Database commit runs
  |
  v
Backend broadcasts lead score update
  |
  v
Frontend refreshes data
```

### 22.2 Login Flow

```text
User enters email and password
  |
  v
Frontend calls POST /auth/login
  |
  v
Backend finds active user by email
  |
  v
Backend verifies bcrypt password hash
  |
  v
Backend creates JWT token
  |
  v
Frontend stores token in localStorage
  |
  v
Future requests include Authorization header
```

### 22.3 AI Refresh Flow

```text
User clicks AI refresh
  |
  v
Frontend calls POST /webhooks/lead-enrichment
  |
  v
Backend enriches lead and stores metadata
  |
  v
Frontend calls POST /webhooks/lead-score
  |
  v
Backend scores lead, updates category, and assigns owner
  |
  v
Backend broadcasts lead score update
  |
  v
Frontend refreshes data
```

### 22.4 Email Generation Flow

```text
User selects lead
  |
  v
User chooses email template
  |
  v
Frontend calls POST /emails/generate
  |
  v
Backend loads lead
  |
  v
Backend generates AI or fallback email
  |
  v
Backend creates tracking token
  |
  v
Backend stores Email row
  |
  v
Backend stores email tracking metadata on lead
  |
  v
Frontend displays subject and body
  |
  v
User clicks Send
  |
  v
Browser opens mailto link
```

### 22.5 CSV Import Flow

```text
Logged-in admin or manager selects CSV
  |
  v
Frontend uploads file to POST /leads/import
  |
  v
Backend validates .csv extension
  |
  v
Backend creates in-memory import job
  |
  v
Background task parses CSV
  |
  v
Each valid row is scored, saved, and assigned
  |
  v
Backend broadcasts import completion or failure
  |
  v
Frontend refreshes data after WebSocket message
```

### 22.6 Analytics Flow

```text
Frontend calls GET /analytics/overview
  |
  v
Backend verifies JWT token and role
  |
  v
Backend loads leads and emails
  |
  v
Backend calculates funnel, source, AI, and routing metrics
  |
  v
Frontend renders charts with Recharts
```

## 23. Docker Compose

Docker Compose is configured in:

```text
docker-compose.yml
```

It defines three services:

- `postgres`
- `backend`
- `frontend`

### 23.1 PostgreSQL Service

The PostgreSQL service uses:

```text
postgres:16-alpine
```

It configures:

- database: `ai_crm`
- user: `postgres`
- password: `postgres`

It maps:

```text
5433:5432
```

It stores database files in the named volume:

```text
postgres_data
```

It also includes a health check using `pg_isready`.

### 23.2 Backend Service

The backend builds from:

```text
./backend
```

It depends on the PostgreSQL service being healthy.

It exposes:

```text
8000:8000
```

It passes AI-related environment variables and `DATABASE_URL`.

It mounts these folders into the container:

- `./backend/app`
- `./backend/services`
- `./backend/alembic`
- `./backend/workflows`

### 23.3 Frontend Service

The frontend builds from:

```text
./frontend
```

It depends on the backend service.

It exposes:

```text
5173:5173
```

It passes:

```text
VITE_API_URL
```

It mounts the frontend source and `index.html`.

## 24. Alembic Migrations

Alembic is configured through:

```text
backend/alembic.ini
backend/alembic/
```

The migration versions included are:

```text
20260708_0001_initial_crm_schema.py
20260708_0002_add_lead_metadata.py
20260708_0003_growth_features.py
```

Based on the filenames and project structure, these migrations represent:

- initial CRM schema
- lead metadata additions
- growth features such as users, assignment, and tracking

The README states that the backend runs Alembic migrations on Docker startup. The current `main.py` also calls `initialize_database()`, which creates tables from models at startup.

## 25. n8n Workflow Files

Workflow files are included under:

```text
backend/workflows/
```

The files are:

- `main_lead_processing.workflow.json`
- `lead_enrichment_subworkflow.workflow.json`
- `email_personalization_subworkflow.workflow.json`
- `task_priority_subworkflow.workflow.json`
- `error_retry_handler.workflow.json`

These workflows are intended to be imported into n8n. They connect external automation flows to CRM webhook endpoints.

The README says to configure:

```text
CRM_API_BASE_URL
```

Optional enrichment provider settings are:

```text
COMPANY_SCRAPE_URL
DECISION_MAKER_LOOKUP_URL
```

The backend webhook routes provide the API surface needed for these workflows to enrich leads, score leads, generate email copy, update leads, and create tasks.

## 26. CORS

CORS is configured in `backend/app/main.py`.

The allowed origins come from:

```text
FRONTEND_ORIGINS
```

The default value is:

```text
http://localhost:5173,http://127.0.0.1:5173
```

This is required because the frontend and backend run on different ports. Without CORS configuration, the browser would block frontend requests to the backend.

## 27. Error Handling

The backend uses FastAPI `HTTPException` for expected error cases.

Important status codes used by the project include:

- `400 Bad Request` for invalid CSV file type or invalid score range filters
- `401 Unauthorized` for invalid login or token problems
- `403 Forbidden` for insufficient role permissions
- `404 Not Found` for missing leads, tasks, or import jobs
- `409 Conflict` for duplicate users or duplicate lead emails
- `429 Too Many Requests` for AI rate-limit failures
- `204 No Content` for successful lead deletion

The frontend API client parses error responses and throws JavaScript errors. The context and components display those errors through the top-level alert.

## 28. Security Concepts

The project includes these security-related features:

- Password hashing with bcrypt
- JWT access tokens
- Role-based route protection
- Email uniqueness for users and leads
- Pydantic request validation
- CORS origin configuration
- Environment variables for secrets and provider keys

Important production considerations still remain:

- Replace the default `JWT_SECRET_KEY`
- Use HTTPS in deployment
- Store secrets outside source control
- Add refresh-token or session-expiration handling if needed
- Add audit logs for sensitive changes
- Add stricter upload size validation for CSV imports
- Add persistent rate limiting if running multiple backend instances
- Use a real email provider for report delivery and outreach sending

## 29. Current Limitations

The project is functional as a starter AI CRM, but some areas are intentionally simple:

- Import job state is stored only in memory
- WebSocket connections are stored only in memory
- AI cache and rate limiter are stored only in memory
- Reporting email delivery is a placeholder
- Generated email sending uses `mailto:` instead of a backend email provider
- Analytics are calculated in Python after loading rows, which may need optimization for large datasets
- The frontend has login but no visible registration form
- The frontend is a single-page dashboard without React Router
- There are no automated test files in the current repository
- The default local backend database URL expects PostgreSQL on port `5433`

## 30. Strengths of the Project

The project has several strong implementation points:

- Clear separation between frontend and backend
- FastAPI routes are organized in a single readable API file
- SQLAlchemy models define clear relationships between leads, tasks, emails, and users
- Pydantic schemas validate API input and output
- AI features work even without provider keys through fallback logic
- Lead assignment is automatic and stored in metadata
- Email tracking data model and endpoints are implemented
- CSV import includes validation, duplicate skipping, scoring, and assignment
- JWT authentication and role-based authorization are implemented
- Analytics are exposed through a dedicated endpoint and visualized in the frontend
- WebSockets allow the frontend to refresh after backend updates
- Docker Compose provides a complete local stack
- n8n workflow files are included for automation integration

## 31. Recommended Future Improvements

Recommended improvements based on the current project state:

1. Add backend tests for authentication, lead CRUD, scoring fallback, imports, and permissions.
2. Add frontend tests for forms, table filters, authentication state, and error handling.
3. Add a visible registration or admin user creation workflow in the frontend.
4. Persist import jobs in the database instead of memory.
5. Move AI cache and rate limiting to Redis for multi-instance deployment.
6. Add pagination to leads, tasks, and emails.
7. Add search and filter parameters to backend task and email endpoints where useful.
8. Add a real email provider for report sending and outreach sending.
9. Add audit logs for lead updates, score changes, imports, and assignment changes.
10. Add richer user management for admins.
11. Add deployment-specific documentation for Render and Docker environments.
12. Add stronger CSV validation, preview, and file size limits.
13. Add database indexes for common analytics and filtering fields.
14. Add background job infrastructure for long-running import or AI workflows.
15. Add production monitoring and structured logs.

## 32. Final Summary

AI CRM is a full-stack CRM application built with React, Vite, FastAPI, SQLAlchemy, PostgreSQL, and optional AI provider integrations.

The backend manages leads, tasks, emails, users, analytics, imports, webhooks, reporting summaries, AI scoring, AI enrichment, email generation, and WebSocket updates.

The frontend presents a single-page CRM command center with KPI cards, analytics charts, lead management, lead details, authentication, CSV import, report triggering, task management, and email drafting.

The AI layer supports OpenAI and Claude when keys are configured. If no provider is available, deterministic fallback logic keeps lead scoring, enrichment, and email generation usable.

The system is suitable as a strong starter CRM project. It already includes the main building blocks of an AI-assisted sales workflow, while leaving clear future paths for production hardening, persistent background jobs, real email delivery, advanced analytics, and automated tests.
