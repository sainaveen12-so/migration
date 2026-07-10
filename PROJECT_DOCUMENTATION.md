# MigrateAI — Complete Project Documentation

**AI Code Migration Tool**  
Version 1.0.0  
A production-ready platform to upload legacy codebases, analyze architecture, migrate between languages/frameworks, and generate documentation — powered by multiple AI providers.

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [Core Features](#5-core-features)
6. [User Roles & Authentication](#6-user-roles--authentication)
7. [Application Workflow](#7-application-workflow)
8. [Database Design](#8-database-design)
9. [AI Provider System](#9-ai-provider-system)
10. [Supported Languages & Migrations](#10-supported-languages--migrations)
11. [API Reference](#11-api-reference)
12. [Frontend Pages](#12-frontend-pages)
13. [Background Jobs (Celery)](#13-background-jobs-celery)
14. [Environment Variables](#14-environment-variables)
15. [How to Run](#15-how-to-run)
16. [Docker Services](#16-docker-services)
17. [Deployment & CI/CD](#17-deployment--cicd)
18. [Monitoring & Health](#18-monitoring--health)
19. [Design Principles](#19-design-principles)
20. [Limitations & Production Notes](#20-limitations--production-notes)

---

## 1. What Is This Project?

**MigrateAI** is a full-stack web application that helps development teams:

- **Upload** source code (ZIP file or GitHub repository)
- **Analyze** project structure, languages, frameworks, APIs, and complexity
- **Migrate** code from one stack to another using AI (e.g., Java → FastAPI, React → Next.js)
- **Interact** with an AI chat assistant about the codebase
- **Refactor**, detect bugs, generate tests, and produce documentation
- **Visualize** architecture with interactive diagrams
- **Track** migration jobs, versions, notifications, and AI usage costs

The system is built with **clean architecture** on the backend (repository pattern, dependency injection, service layer) and a modern **Next.js** frontend.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                 │
│                    http://localhost:3000                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP / REST
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 15)                             │
│   React 19 · TypeScript · Tailwind · Monaco Editor · React Flow     │
│   Zustand (state) · React Query (server data) · Axios (API client)  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ /api/v1/*
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                                 │
│   Python 3.12 · JWT Auth · Swagger Docs · Prometheus Metrics        │
│                                                                      │
│   ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌───────────────┐  │
│   │ API Layer│→ │Service Layer│→ │Repository│→ │ SQLite (async)│  │
│   └──────────┘  └─────────────┘  └──────────┘  └───────────────┘  │
│                         │                                            │
│                         ▼                                            │
│              ┌─────────────────────┐                                │
│              │  AI Provider Factory │                                │
│              │ OpenAI·Gemini·Claude │                                │
│              │       · Ollama       │                                │
│              └─────────────────────┘                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Task queue
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CELERY WORKERS                                    │
│   Analysis · Migration · Documentation · Test Generation          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
     ┌─────────────────┐              ┌─────────────────┐
     │  Redis (broker)  │              │  File Storage   │
     │  + result cache  │              │  uploads/ data/ │
     └─────────────────┘              └─────────────────┘
```

### Request Flow Example (Migration)

1. User uploads a ZIP file via the frontend
2. Backend stores files in `uploads/` and records metadata in SQLite
3. User clicks **Analyze** → Celery task scans code structure
4. User selects migration target (e.g., Java → FastAPI) and clicks **Migrate**
5. Celery worker calls AI provider for each source file
6. Migrated code is saved; user downloads the result as ZIP
7. Notification is sent when the job completes or fails

---

## 3. Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| Next.js 15 | React framework with App Router |
| React 19 | UI library |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| shadcn/ui (Radix) | UI components |
| React Query | Server state & caching |
| Zustand | Client state (auth, notifications) |
| Monaco Editor | Code editor with syntax highlighting |
| React Flow | Architecture diagrams |
| Axios | HTTP client with JWT interceptors |

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.12 | Runtime |
| FastAPI | REST API framework |
| SQLAlchemy 2.0 | ORM (async + sync) |
| Alembic | Database migrations |
| SQLite + aiosqlite | Database (file-based) |
| Redis | Celery broker & cache |
| Celery | Background job processing |
| Pydantic | Request/response validation |
| python-jose | JWT tokens |
| passlib/bcrypt | Password hashing |

### AI Providers
| Provider | Default Model | Use Case |
|----------|---------------|----------|
| OpenAI | gpt-4o | General migration & analysis |
| Google Gemini | gemini-1.5-pro | Cost-effective alternative |
| Anthropic Claude | claude-3-5-sonnet | High-quality code reasoning |
| Ollama | llama3.2 | Local/offline models |

### DevOps
| Technology | Purpose |
|------------|---------|
| Docker & Docker Compose | Containerized deployment |
| GitHub Actions | CI/CD pipeline |
| Prometheus | Metrics endpoint |

---

## 4. Project Structure

```
migration/
│
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                   # Application entry point
│   │   ├── core/                     # Config, database, security, deps
│   │   │   ├── config.py             # Environment settings
│   │   │   ├── database.py           # SQLAlchemy async engine
│   │   │   ├── security.py           # JWT & password utilities
│   │   │   ├── deps.py               # FastAPI dependencies (auth)
│   │   │   └── redis.py              # Redis client
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── repositories/             # Data access layer
│   │   ├── services/                 # Business logic
│   │   │   ├── analysis_service.py   # Code analysis engine
│   │   │   ├── migration_service.py  # AI migration logic
│   │   │   ├── ai_service.py         # Chat, explain, refactor, bugs
│   │   │   └── project_service.py    # Project CRUD & uploads
│   │   ├── ai/                       # AI provider strategy pattern
│   │   │   ├── base.py               # Abstract AIProvider interface
│   │   │   ├── factory.py            # Provider factory (runtime switch)
│   │   │   ├── openai_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   ├── claude_provider.py
│   │   │   └── ollama_provider.py
│   │   ├── api/v1/endpoints/         # REST API routes
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── ai.py
│   │   │   └── dashboard.py
│   │   └── tasks/                    # Celery background tasks
│   │       ├── celery_app.py
│   │       └── migration_tasks.py
│   ├── alembic/                      # Database migrations
│   ├── data/                         # SQLite database file (local)
│   ├── uploads/                      # Uploaded & migrated projects
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                         # Next.js frontend
│   └── src/
│       ├── app/                      # Pages (App Router)
│       │   ├── login/ signup/ forgot-password/
│       │   ├── dashboard/
│       │   ├── projects/ [id]/
│       │   ├── search/
│       │   └── settings/
│       ├── components/
│       │   ├── ui/                   # Button, Card, Input, etc.
│       │   ├── layout/               # Sidebar, Header
│       │   ├── dashboard/            # Stats widgets
│       │   ├── editor/               # Monaco code editor
│       │   ├── chat/                 # AI chat panel
│       │   └── diagrams/             # React Flow viewer
│       ├── lib/
│       │   ├── api.ts                # API client (all endpoints)
│       │   └── utils.ts
│       └── stores/                   # Zustand stores
│
├── docker-compose.yml                # All services orchestration
├── scripts/deploy.sh                 # One-command deployment
├── .github/workflows/ci-cd.yml       # GitHub Actions pipeline
├── README.md                         # Quick start guide
└── PROJECT_DOCUMENTATION.md          # This document
```

---

## 5. Core Features

### 5.1 Dashboard
Displays at-a-glance metrics:
- Total projects, files, lines of code
- Migration status breakdown (pending, analyzing, migrated, failed)
- AI usage count, token usage, cost analytics
- Recent projects list

### 5.2 Project Management
| Action | Description |
|--------|-------------|
| Create Project | Name, description, source/target language |
| Upload ZIP | Upload a compressed source codebase |
| Clone GitHub | Clone a public/private repo by URL |
| Browse Files | Tree view of all source files |
| Analyze | Detect language, framework, APIs, dependencies |
| Migrate | AI-powered code conversion to target stack |
| Download | Download migrated project as ZIP |
| Delete | Remove project and associated files |
| Version History | Track migration versions |

### 5.3 Code Analysis
After upload, the analyzer detects:
- **Programming language** (Java, Python, C#, JS, TS, PHP, SQL, etc.)
- **Framework** (Spring Boot, Flask, Django, React, Angular, .NET, etc.)
- **Dependencies** (from package.json, requirements.txt, pom.xml, etc.)
- **Folder structure** (tree view)
- **REST APIs** (route decorators and mappings)
- **Database** (PostgreSQL, MySQL, SQL Server, Oracle, MongoDB, SQLite)
- **ORM** (SQLAlchemy, Hibernate, Django ORM, TypeORM, etc.)
- **Controllers, Services, Repositories, Utilities**
- **Complexity score** (0–10 scale)
- **Project summary** and **architecture overview**

### 5.4 AI Chat
Context-aware chat interface. Users can ask:
- "Explain this project"
- "Explain this class / function"
- "Where is authentication implemented?"
- "How is database connection created?"
- "Explain API flow"
- "Find bugs"
- "Generate documentation"

Chat history is stored per project.

### 5.5 Code Explanation (per file)
Click **Explain** on any file to get:
- Purpose
- Business logic
- Inputs & outputs
- Complexity assessment
- Dependencies

### 5.6 AI Refactoring
| Type | What It Does |
|------|--------------|
| rename | Meaningful variable names |
| extract_method | Extract repeated logic |
| performance | Performance optimization |
| solid | Apply SOLID principles |
| clean_code | Clean code improvements |
| security | Security hardening |
| async | Async/await conversion |

### 5.7 Bug Detection
Scans for:
- Null pointer issues
- Memory issues
- Performance problems
- Security vulnerabilities
- Duplicate code
- Dead code
- Unused imports

### 5.8 Test Generation
Generates tests in:
- **pytest** (Python)
- **JUnit** (Java)
- **Jest** (JavaScript/TypeScript)
- API tests, integration tests, Postman collections

### 5.9 Documentation Generation
Produces:
- README
- Swagger / API documentation
- Architecture document
- Deployment guide
- Technical Design Document (TDD)

### 5.10 Architecture Visualization
Auto-generates React Flow diagrams:
- **Flow Diagram** — application flow
- **Dependency Graph** — module dependencies
- **Class Diagram** — class relationships
- **Sequence Diagram** — API call sequences

### 5.11 Global Search
Search across:
- Projects (by name/description)
- Files (by name, path, content)
- Methods, classes, APIs, SQL

### 5.12 Notifications
Real-time notifications for:
- Job started
- Migration completed / failed
- Documentation generated
- Tests generated

---

## 6. User Roles & Authentication

### Authentication Flow
```
Register → JWT access token (30 min) + refresh token (7 days)
Login    → Same token pair
Refresh  → New access token using refresh token
Forgot   → Password reset token (1 hour expiry)
```

All protected API routes require: `Authorization: Bearer <access_token>`

### Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all resources |
| **Developer** | Create/manage own projects, run migrations |
| **Reviewer** | View projects, review migrations (read-focused) |

Role checks are enforced via `require_roles()` dependency in the backend.

---

## 7. Application Workflow

### Typical User Journey

```
1. SIGN UP / LOGIN
        │
        ▼
2. CREATE PROJECT
        │
        ▼
3. UPLOAD ZIP  or  CLONE GITHUB
        │
        ▼
4. ANALYZE PROJECT  (background job)
        │
        ├── View analysis results
        ├── Browse source files in Monaco editor
        ├── Chat with AI about the codebase
        └── View architecture diagrams
        │
        ▼
5. SELECT MIGRATION TARGET
   (e.g., Spring Boot → FastAPI)
        │
        ▼
6. START MIGRATION  (background job)
        │
        ├── Progress tracked via job status API
        └── Notification on completion
        │
        ▼
7. REVIEW MIGRATED CODE
   (diff viewer: original vs migrated)
        │
        ▼
8. OPTIONAL: Generate tests, docs, refactor
        │
        ▼
9. DOWNLOAD MIGRATED PROJECT (ZIP)
```

---

## 8. Database Design

**Engine:** SQLite  
**File:** `./data/migration.db` (local) or `/app/data/migration.db` (Docker)

### Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts, roles, credentials |
| `projects` | Migration projects metadata & status |
| `project_files` | Individual source/migrated files |
| `migration_jobs` | Background job tracking (Celery) |
| `chat_messages` | AI chat history per project |
| `ai_responses` | Stored AI prompt/response pairs |
| `ai_usage` | Token usage & cost tracking |
| `audit_logs` | User action audit trail |
| `project_versions` | Migration version snapshots |
| `notifications` | User notifications |

### Key Relationships

```
users ──1:N──► projects ──1:N──► project_files
                  │
                  ├──1:N──► migration_jobs
                  ├──1:N──► chat_messages
                  └──1:N──► project_versions

users ──1:N──► ai_usage
users ──1:N──► notifications
users ──1:N──► audit_logs
```

### Project Status Lifecycle

```
pending → analyzing → analyzed → migrating → migrated
                              └──────────────► failed
```

---

## 9. AI Provider System

The backend uses the **Strategy Pattern** so AI providers can be swapped without code changes.

```
AIProvider (abstract)
    ├── OpenAIProvider
    ├── GeminiProvider
    ├── ClaudeProvider
    └── OllamaProvider

AIProviderFactory
    ├── get_provider(name)     → returns provider instance
    ├── set_default_provider() → switch at runtime
    └── list_providers()       → ["openai","gemini","claude","ollama"]
```

### Switching Providers

**Via Settings page (frontend):** Select provider and model  
**Via API:**
```http
POST /api/v1/ai/providers/switch
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider": "claude",
  "model": "claude-3-5-sonnet-20241022"
}
```

**Via environment variable:**
```env
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

No application restart is required when switching via API.

---

## 10. Supported Languages & Migrations

### Languages Analyzed
Java · Spring Boot · Python · Flask · Django · C# · .NET · JavaScript · TypeScript · Angular · React · PHP · Node.js · SQL

### Migration Paths

| Source | Target | Notes |
|--------|--------|-------|
| Java | FastAPI (Python) | Controllers → routers, services preserved |
| Spring Boot | FastAPI (Python) | Full framework mapping |
| Flask | FastAPI (Python) | Routes → async endpoints |
| React | Next.js (TypeScript) | App Router, server components |
| Angular | React (TypeScript) | Components → hooks |
| JavaScript | TypeScript | Type annotations added |
| C# / .NET | Python (FastAPI) | Business logic preserved |
| SQL Server | PostgreSQL SQL | T-SQL conversion |
| Oracle | PostgreSQL SQL | PL/SQL conversion |
| PHP | Node.js (Express) | Framework mapping |

---

## 11. API Reference

**Base URL:** `http://localhost:8000/api/v1`  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)  
**ReDoc:** `http://localhost:8000/redoc`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, get tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/forgot-password` | Request reset link |
| POST | `/auth/reset-password` | Reset password with token |

### Dashboard & System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/stats` | Dashboard metrics |
| GET | `/health` | System health check |
| GET | `/search?q=` | Global search |
| GET | `/notifications` | User notifications |
| PATCH | `/notifications/{id}/read` | Mark notification read |
| GET | `/jobs/{id}` | Get job status |
| GET | `/jobs/project/{id}` | List project jobs |

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects` | List all projects |
| POST | `/projects` | Create project |
| GET | `/projects/{id}` | Get project details |
| PATCH | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |
| POST | `/projects/{id}/upload` | Upload ZIP file |
| POST | `/projects/{id}/clone-github` | Clone GitHub repo |
| POST | `/projects/{id}/analyze` | Start analysis job |
| GET | `/projects/{id}/analysis` | Get analysis results |
| POST | `/projects/{id}/migrate` | Start migration job |
| GET | `/projects/{id}/files` | List project files |
| GET | `/projects/{id}/files/{file_id}` | Get file with content |
| GET | `/projects/{id}/download` | Download migrated ZIP |
| GET | `/projects/{id}/versions` | List versions |

### AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ai/providers` | List AI providers |
| POST | `/ai/providers/switch` | Switch active provider |
| POST | `/ai/projects/{id}/chat` | Send chat message |
| GET | `/ai/projects/{id}/chat` | Get chat history |
| POST | `/ai/projects/{id}/explain` | Explain a file |
| POST | `/ai/projects/{id}/refactor` | Refactor code |
| POST | `/ai/projects/{id}/bugs` | Detect bugs |
| POST | `/ai/projects/{id}/generate-tests` | Generate tests (async) |
| POST | `/ai/projects/{id}/generate-docs` | Generate docs (async) |
| GET | `/ai/projects/{id}/diagrams` | Get architecture diagrams |

---

## 12. Frontend Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Redirect | Redirects to `/dashboard` |
| `/login` | Login | Email/password sign in |
| `/signup` | Sign Up | Create new account |
| `/forgot-password` | Forgot Password | Request password reset |
| `/dashboard` | Dashboard | Stats, recent projects |
| `/projects` | Projects List | Create, view, delete projects |
| `/projects/[id]` | Project Detail | Files, editor, chat, diagrams, migration |
| `/search` | Global Search | Search projects and files |
| `/settings` | Settings | AI provider configuration |

### Project Detail Tabs

| Tab | Features |
|-----|----------|
| **Files** | File tree, migration controls, project status |
| **Editor** | Monaco editor, explain/refactor/bug buttons, diff viewer |
| **AI Chat** | Contextual chat with quick prompts |
| **Diagrams** | Flow, dependency, class, sequence diagrams |
| **Analysis** | Language, framework, APIs, dependencies, complexity |

---

## 13. Background Jobs (Celery)

Long-running operations run asynchronously via Celery workers.

| Task | Trigger | What It Does |
|------|---------|--------------|
| `analyze_project` | POST `/projects/{id}/analyze` | Scans all files, detects stack, saves analysis |
| `migrate_project` | POST `/projects/{id}/migrate` | AI-migrates each file to target stack |
| `generate_documentation` | POST `/ai/projects/{id}/generate-docs` | Generates README, API docs, architecture doc |
| `generate_tests` | POST `/ai/projects/{id}/generate-tests` | Generates test files per source file |

### Job Statuses
`pending` → `running` → `completed` or `failed`

Poll job progress: `GET /api/v1/jobs/{job_id}`

---

## 14. Environment Variables

Copy `backend/.env.example` to `.env` at the project root.

### Required for Basic Operation

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (change me) | JWT signing secret — **must change in production** |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/migration.db` | Async database URL |
| `DATABASE_URL_SYNC` | `sqlite:///./data/migration.db` | Sync database URL (Celery) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery message broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery result store |

### AI Provider Keys (at least one required)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) |
| `DEFAULT_AI_PROVIDER` | Default provider: `openai`, `gemini`, `claude`, `ollama` |

### Optional

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT for private repo cloning |
| `UPLOAD_DIR` | File upload directory (default: `./uploads`) |
| `MAX_UPLOAD_SIZE_MB` | Max ZIP upload size (default: 500 MB) |
| `CORS_ORIGINS` | Allowed frontend origins |
| `FRONTEND_URL` | Used in password reset emails |

### Frontend

Copy `frontend/.env.local.example` to `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 15. How to Run

### Option A — Docker (Recommended)

```bash
# 1. Clone the repository
git clone <repo-url>
cd migration

# 2. Configure environment
cp backend/.env.example .env
# Edit .env — add SECRET_KEY and at least one AI API key

# 3. Start all services
docker compose up -d --build

# Or use the deploy script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**Access points after startup:**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/v1/health |
| Prometheus Metrics | http://localhost:8000/metrics |

### Option B — Local Development

**Terminal 1 — Redis:**
```bash
docker compose up -d redis
```

**Terminal 2 — Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
mkdir data
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Terminal 3 — Celery Worker:**
```bash
cd backend
venv\Scripts\activate
celery -A app.tasks.celery_app worker --loglevel=info
```

**Terminal 4 — Frontend:**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### Option C — Local AI with Ollama

```bash
docker compose --profile local-ai up -d ollama
docker exec -it <ollama-container> ollama pull llama3.2
```

Then set in `.env`:
```env
DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 16. Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI application |
| `frontend` | 3000 | Next.js application |
| `redis` | 6379 | Message broker & cache |
| `celery-worker` | — | Background job processor |
| `celery-beat` | — | Scheduled task runner |
| `ollama` | 11434 | Local AI (optional profile) |

### Persistent Volumes

| Volume | Mount Point | Contents |
|--------|-------------|----------|
| `sqlite_data` | `/app/data` | SQLite database file |
| `upload_data` | `/app/uploads` | Uploaded & migrated projects |
| `redis_data` | `/data` | Redis persistence |
| `ollama_data` | `/root/.ollama` | Downloaded AI models |

---

## 17. Deployment & CI/CD

### GitHub Actions Pipeline (`.github/workflows/ci-cd.yml`)

Triggered on push to `main` or `develop`:

1. **backend-test** — Install deps, run Alembic migrations on SQLite, compile Python
2. **frontend-build** — `npm ci`, `npm run build`, `npm run lint`
3. **docker-build** — Build & push images to GitHub Container Registry (main branch only)

### AWS Deployment (Production)

| AWS Service | Purpose |
|-------------|---------|
| ECS / Fargate | Run backend & frontend containers |
| ElastiCache | Redis for Celery |
| S3 | Store uploaded projects (replace local `uploads/`) |
| ALB | Load balance traffic |
| Secrets Manager | Store API keys and `SECRET_KEY` |
| CloudWatch | Logs and monitoring |

For production at scale, consider replacing SQLite with **PostgreSQL (RDS)** by updating `DATABASE_URL` only — no code changes required.

---

## 18. Monitoring & Health

### Health Check
```http
GET /api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "healthy",
  "redis": "healthy",
  "celery": "healthy"
}
```

### Prometheus Metrics
```
GET /metrics
```
Exposes standard Prometheus metrics for monitoring dashboards.

### Structured Logging
Backend uses `structlog` for JSON-formatted logs in production and readable console output in debug mode.

---

## 19. Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Clean Architecture** | API → Service → Repository → Model layers |
| **SOLID** | Single-responsibility services, provider abstraction |
| **Repository Pattern** | All DB access through repository classes |
| **Strategy Pattern** | Swappable AI providers via factory |
| **Dependency Injection** | FastAPI `Depends()` for auth, DB sessions |
| **Async-First** | FastAPI + SQLAlchemy async for API; sync for Celery |
| **Separation of Concerns** | Frontend only talks to REST API; no direct DB access |

---

## 20. Limitations & Production Notes

### Current Limitations
- **SQLite** is file-based and suited for development/small deployments. Not ideal for high-concurrency production.
- **AI migration quality** depends on the chosen model and source code complexity. Large files (>50 KB) are copied as-is.
- **Email** for password reset requires SMTP configuration (`MAIL_*` variables).
- **GitHub cloning** of private repos requires `GITHUB_TOKEN`.

### Before Going to Production
1. Change `SECRET_KEY` to a strong random value (32+ characters)
2. Set `DEBUG=false`
3. Configure at least one AI provider API key
4. Consider PostgreSQL for the database at scale
5. Set up proper SMTP for password reset emails
6. Configure HTTPS via reverse proxy (nginx / ALB)
7. Set `CORS_ORIGINS` to your production frontend URL only
8. Review upload size limits (`MAX_UPLOAD_SIZE_MB`)

### Getting Help
- API documentation: http://localhost:8000/docs
- Health status: http://localhost:8000/api/v1/health
- Check Celery worker logs: `docker compose logs celery-worker`
- Check backend logs: `docker compose logs backend`

---

*MigrateAI v1.0.0 — Built with FastAPI, Next.js, and multi-provider AI.*
