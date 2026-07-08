# AI CRM

Full-stack AI CRM starter with a React frontend, FastAPI backend, and PostgreSQL database.

## Services

- Frontend: React + Vite on `http://localhost:5173`
- Backend: FastAPI on `http://localhost:8000`
- Database: PostgreSQL on `localhost:5432`

## Environment

Copy `.env.example` to `.env` and fill in API keys when needed:

```bash
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ai_crm
OPENAI_API_KEY=
CLAUDE_API_KEY=
AI_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
CLAUDE_MODEL=claude-3-5-haiku-latest
AI_CACHE_TTL_SECONDS=300
AI_RATE_LIMIT_PER_MINUTE=30
VITE_API_URL=http://localhost:8000
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REPORTING_INTERVAL_MINUTES=1440
REPORTING_EMAIL_TO=
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PUBLIC_API_BASE_URL=http://localhost:8000
```

## Run With Docker

```bash
docker compose up --build
```

The backend runs Alembic migrations on startup.

## Backend Local Development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run migrations locally from `backend/`:

```bash
alembic upgrade head
```

## Frontend Local Development

```bash
cd frontend
npm install
npm run dev
```

## API Surface

- `POST /leads` creates a lead and applies local AI scoring when no score is supplied
- `GET /leads` lists leads with `status`, `category`, `score`, `min_score`, and `max_score` filters
- `GET /leads/{id}`, `PUT /leads/{id}`, `DELETE /leads/{id}` manage individual leads
- `POST /tasks` creates a task, auto-generating a description from the lead when omitted
- `GET /tasks`, `PUT /tasks/{id}` manage tasks
- `POST /emails/generate` creates generated email copy for a lead
- `GET /emails` lists generated emails
- `POST /webhooks/lead-enrichment` enriches a lead and stores AI insights in lead metadata
- `POST /webhooks/lead-score` scores a lead and updates `lead_score`, `category`, and metadata
- `POST /webhooks/generate-email` creates personalized outreach email copy for n8n workflows
- `POST /webhooks/update-lead` receives n8n callbacks and stores workflow results in lead metadata
- `POST /webhooks/create-task` receives n8n callbacks and creates score-prioritized follow-up tasks
- `WS /ws/leads` streams lead score and import updates
- `POST /leads/capture` captures landing page leads with AI scoring and assignment
- `POST /leads/import` queues CSV imports with AI processing
- `GET /analytics/overview` returns funnel, source, AI, and routing metrics
- `GET /emails/track/open/{token}.png` and `GET /emails/track/click/{token}` track email engagement
- `POST /auth/register`, `POST /auth/login`, `GET /auth/me` provide JWT authentication
- `POST /reports/send-summary` triggers a report summary

## Render Deploy

Use `render.yaml` from the repository root. Configure provider secrets for `OPENAI_API_KEY`, `CLAUDE_API_KEY`, and `REPORTING_EMAIL_TO` in Render.

## n8n Workflows

Import the JSON files from `backend/workflows/` into n8n:

- `main_lead_processing.workflow.json`
- `lead_enrichment_subworkflow.workflow.json`
- `email_personalization_subworkflow.workflow.json`
- `task_priority_subworkflow.workflow.json`
- `error_retry_handler.workflow.json`

Set `CRM_API_BASE_URL` in n8n to the backend base URL. Optional enrichment providers can be connected with `COMPANY_SCRAPE_URL` and `DECISION_MAKER_LOOKUP_URL`.
