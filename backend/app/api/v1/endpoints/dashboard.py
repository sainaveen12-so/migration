from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, DBSession
from app.repositories.job_repository import AIUsageRepository, JobRepository, NotificationRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.dashboard import DashboardStats, HealthResponse, JobResponse, NotificationResponse, SearchResponse, SearchResult
from app.services.project_service import ProjectService
from app.core.config import settings

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: CurrentUser, db: DBSession):
    svc = ProjectService(ProjectRepository(db))
    stats = await svc.get_dashboard_stats(current_user.id)
    usage_repo = AIUsageRepository(db)
    usage = await usage_repo.get_stats(current_user.id)

    return DashboardStats(
        total_projects=stats["total_projects"],
        total_files=stats["total_files"],
        total_lines_of_code=stats["total_lines_of_code"],
        migration_status=stats["migration_status"],
        ai_usage_count=usage["count"],
        total_tokens=usage["total_tokens"],
        total_cost=usage["total_cost"],
        recent_projects=stats["recent_projects"],
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, current_user: CurrentUser, db: DBSession):
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(job.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")
    return job


@router.get("/jobs/project/{project_id}", response_model=list[JobResponse])
async def get_project_jobs(project_id: int, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await JobRepository(db).get_by_project(project_id)


@router.get("/notifications", response_model=list[NotificationResponse])
async def get_notifications(current_user: CurrentUser, db: DBSession, unread_only: bool = False):
    return await NotificationRepository(db).get_by_user(current_user.id, unread_only)


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, current_user: CurrentUser, db: DBSession):
    await NotificationRepository(db).mark_read(notification_id, current_user.id)
    return {"status": "read"}


@router.get("/search", response_model=SearchResponse)
async def global_search(q: str, current_user: CurrentUser, db: DBSession, limit: int = 50):
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    project_repo = ProjectRepository(db)
    results: list[SearchResult] = []

    projects = await project_repo.get_all(current_user.id, limit=20)
    for p in projects:
        if q.lower() in p.name.lower() or (p.description and q.lower() in p.description.lower()):
            results.append(SearchResult(type="project", id=p.id, name=p.name, project_id=p.id, project_name=p.name))

    files = await project_repo.search_files(current_user.id, q, limit)
    for f in files:
        project = await project_repo.get_by_id(f.project_id)
        snippet = None
        if f.content and q.lower() in f.content.lower():
            idx = f.content.lower().find(q.lower())
            snippet = f.content[max(0, idx - 50): idx + len(q) + 50]
        results.append(
            SearchResult(
                type="file",
                id=f.id,
                name=f.file_name,
                path=f.file_path,
                project_id=f.project_id,
                project_name=project.name if project else None,
                snippet=snippet,
            )
        )

    return SearchResponse(query=q, results=results[:limit], total=len(results))


@router.get("/health", response_model=HealthResponse)
async def health_check(db: DBSession):
    db_status = "healthy"
    redis_status = "healthy"
    celery_status = "unknown"

    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    try:
        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.ping()
    except Exception:
        redis_status = "unhealthy"

    try:
        from app.tasks.celery_app import celery_app
        inspect = celery_app.control.inspect()
        if inspect.ping():
            celery_status = "healthy"
        else:
            celery_status = "no_workers"
    except Exception:
        celery_status = "unhealthy"

    overall = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.APP_VERSION,
        database=db_status,
        redis=redis_status,
        celery=celery_status,
    )
