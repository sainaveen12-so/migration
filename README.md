# MigrateAI - AI Code Migration Tool

> **Full documentation:** See [PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md) for the complete project guide.

A production-ready, full-stack AI-powered code migration platform. Upload legacy codebases, analyze architecture, migrate between languages/frameworks, and generate documentation — all powered by multiple AI providers.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Next.js 15 │────▶│   FastAPI    │────▶│   SQLite    │
│  Frontend   │     │   Backend    │     │             │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐
                    │    Redis     │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │    Celery    │
                    │   Workers    │
                    └──────────────┘
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui, React Query, Zustand, Monaco Editor, React Flow |
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic, Celery |
| **Database** | SQLite, Redis |
| **AI** | OpenAI, Google Gemini, Anthropic Claude, Ollama |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

## Features

- **Authentication** — JWT login, signup, forgot password, role-based access (Admin, Developer, Reviewer)
- **Project Management** — Create, upload ZIP, clone GitHub, browse files, download migrated output
- **Code Analysis** — Language/framework detection, dependency mapping, REST API discovery, complexity scoring
- **AI Migration** — Java→FastAPI, Spring Boot→FastAPI, React→Next.js, Angular→React, JS→TS, .NET→Python, and more
- **AI Chat** — Ask questions about projects, classes, functions, auth flows, database connections
- **Code Tools** — Explain, refactor, bug detection, test generation, documentation generation
- **Architecture Viz** — Flow, dependency, class, and sequence diagrams via React Flow
- **Background Jobs** — Async migration, analysis, docs, and tests via Celery
- **Version History** — Track migration versions with compare and rollback
- **Global Search** — Search projects, files, methods, classes, APIs
- **Monitoring** — Health checks, Prometheus metrics, structured logging

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### Docker (Recommended)

```bash
# Clone and deploy
git clone <repo-url>
cd migration

# Configure environment
cp backend/.env.example .env
# Edit .env with your AI API keys

# Start all services
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Or manually:
docker compose up -d --build
```

**Access:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Metrics: http://localhost:8000/metrics

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Start Redis (or use Docker)
docker compose up -d redis

alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Project Structure

```
migration/
├── backend/
│   ├── app/
│   │   ├── ai/              # AI provider strategy pattern
│   │   ├── api/v1/          # REST API endpoints
│   │   ├── core/            # Config, security, database
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── tasks/           # Celery background tasks
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/             # Next.js App Router pages
│       ├── components/      # UI components
│       ├── lib/             # API client, utilities
│       └── stores/          # Zustand state management
├── docker-compose.yml
├── scripts/
└── .github/workflows/
```

## API Documentation

Full Swagger documentation is available at `/docs` when the backend is running.

Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/dashboard/stats` | Dashboard metrics |
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects/{id}/upload` | Upload ZIP |
| POST | `/api/v1/projects/{id}/analyze` | Analyze project |
| POST | `/api/v1/projects/{id}/migrate` | Start migration |
| POST | `/api/v1/ai/projects/{id}/chat` | AI chat |
| GET | `/api/v1/search?q=` | Global search |

## AI Provider Configuration

Switch providers at runtime via API or Settings page:

```bash
# Environment variables
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434

# Or via API
curl -X POST http://localhost:8000/api/v1/ai/providers/switch \
  -H "Authorization: Bearer <token>" \
  -d '{"provider": "claude", "model": "claude-3-5-sonnet-20241022"}'
```

## Supported Migrations

| Source | Target |
|--------|--------|
| Java | FastAPI (Python) |
| Spring Boot | FastAPI (Python) |
| Flask | FastAPI (Python) |
| React | Next.js (TypeScript) |
| Angular | React (TypeScript) |
| JavaScript | TypeScript |
| C# / .NET | Python (FastAPI) |
| SQL Server | PostgreSQL |
| Oracle | PostgreSQL |
| PHP | Node.js |

## AWS Deployment

The application is AWS-ready:

1. **ECS/Fargate** — Use the Docker images from GitHub Container Registry
2. **RDS / managed DB** — Optional: swap SQLite for PostgreSQL in production by updating `DATABASE_URL`
3. **ElastiCache** — Redis for Celery broker and caching
4. **S3** — Store uploaded projects (configure `UPLOAD_DIR` or adapt storage service)
5. **ALB** — Load balance frontend and backend services
6. **Secrets Manager** — Store API keys and `SECRET_KEY`

## Environment Variables

See `backend/.env.example` and `frontend/.env.local.example` for all configuration options.

## License

MIT
