from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.deps import CurrentUser, DBSession
from app.models.user import JobType, ProjectStatus
from app.repositories.job_repository import AuditRepository, JobRepository, NotificationRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    GitHubCloneRequest,
    MigrationRequest,
    ProjectCreate,
    ProjectFileContentResponse,
    ProjectFileResponse,
    ProjectResponse,
    ProjectUpdate,
    ProjectVersionResponse,
)
from app.services.project_service import ProjectService
from app.services.migration_service import MigrationService
from app.tasks.migration_tasks import analyze_project_task, migrate_project_task

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, current_user: CurrentUser, db: DBSession):
    svc = ProjectService(ProjectRepository(db), AuditRepository(db))
    project = await svc.create_project(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        source_language=data.source_language,
        target_language=data.target_language,
        source_framework=data.source_framework,
        target_framework=data.target_framework,
    )
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(current_user: CurrentUser, db: DBSession, skip: int = 0, limit: int = 50):
    repo = ProjectRepository(db)
    return await repo.get_all(current_user.id, skip, limit)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, current_user: CurrentUser, db: DBSession):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate, current_user: CurrentUser, db: DBSession):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await repo.update(project, **data.model_dump(exclude_unset=True))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, current_user: CurrentUser, db: DBSession):
    svc = ProjectService(ProjectRepository(db), AuditRepository(db))
    try:
        await svc.delete_project(project_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/upload")
async def upload_zip(project_id: int, current_user: CurrentUser, db: DBSession, file: UploadFile = File(...)):
    if file.size and file.size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")

    content = await file.read()
    svc = ProjectService(ProjectRepository(db), AuditRepository(db), NotificationRepository(db))
    try:
        return await svc.upload_zip(project_id, current_user.id, content, file.filename or "upload.zip")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/clone-github")
async def clone_github(project_id: int, data: GitHubCloneRequest, current_user: CurrentUser, db: DBSession):
    import os
    import uuid

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    dest_dir = os.path.join(settings.UPLOAD_DIR, str(project_id), str(uuid.uuid4()), "source")
    try:
        MigrationService.clone_github_repo(data.github_url, dest_dir, data.branch, settings.GITHUB_TOKEN)
        from app.services.analysis_service import FileExtractor
        project_root = FileExtractor.get_project_root(dest_dir)
        await repo.update(project, source_path=project_root, github_url=data.github_url, status=ProjectStatus.PENDING)
        if data.name:
            await repo.update(project, name=data.name)
        return {"status": "cloned", "source_path": project_root}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Clone failed: {str(e)}")


@router.post("/{project_id}/analyze")
async def analyze_project(project_id: int, current_user: CurrentUser, db: DBSession, async_mode: bool = True):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project or not project.source_path:
        raise HTTPException(status_code=404, detail="Project not found or no source")

    if async_mode:
        job_repo = JobRepository(db)
        job = await job_repo.create(project_id=project_id, job_type=JobType.ANALYSIS)
        task = analyze_project_task.delay(project_id, job.id, current_user.id)
        await job_repo.update(job, celery_task_id=task.id)
        return {"job_id": job.id, "task_id": task.id, "status": "started"}
    else:
        svc = ProjectService(ProjectRepository(db), NotificationRepository=NotificationRepository(db))
        return await svc.analyze_project(project_id, current_user.id)


@router.get("/{project_id}/files", response_model=list[ProjectFileResponse])
async def list_files(project_id: int, current_user: CurrentUser, db: DBSession):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await repo.get_files(project_id)


@router.get("/{project_id}/files/{file_id}", response_model=ProjectFileContentResponse)
async def get_file(project_id: int, file_id: int, current_user: CurrentUser, db: DBSession):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    file = await repo.get_file(project_id, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.post("/{project_id}/migrate")
async def migrate_project(project_id: int, data: MigrationRequest, current_user: CurrentUser, db: DBSession):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status not in (ProjectStatus.ANALYZED, ProjectStatus.MIGRATED, ProjectStatus.FAILED):
        raise HTTPException(status_code=400, detail="Project must be analyzed before migration")

    job_repo = JobRepository(db)
    job = await job_repo.create(project_id=project_id, job_type=JobType.MIGRATION)
    task = migrate_project_task.delay(project_id, job.id, data.target_language, data.target_framework)
    await job_repo.update(job, celery_task_id=task.id)

    notif_repo = NotificationRepository(db)
    await notif_repo.create(
        user_id=current_user.id,
        title="Migration Started",
        message=f"Migration started for '{project.name}'.",
        notification_type="job_started",
        metadata_json={"project_id": project_id, "job_id": job.id},
    )

    return {"job_id": job.id, "task_id": task.id, "status": "started"}


@router.get("/{project_id}/download")
async def download_migrated(project_id: int, current_user: CurrentUser, db: DBSession):
    import os
    import tempfile

    from fastapi.responses import FileResponse

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project or not project.migrated_path:
        raise HTTPException(status_code=404, detail="Migrated project not found")

    from app.ai.factory import AIProviderFactory
    from app.services.migration_service import MigrationService

    zip_path = os.path.join(tempfile.gettempdir(), f"project_{project_id}_migrated.zip")
    MigrationService(AIProviderFactory.get_provider()).create_zip(project.migrated_path, zip_path)
    return FileResponse(zip_path, filename=f"{project.name}_migrated.zip", media_type="application/zip")


@router.get("/{project_id}/versions", response_model=list[ProjectVersionResponse])
async def list_versions(project_id: int, current_user: CurrentUser, db: DBSession):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await repo.get_versions(project_id)


@router.get("/{project_id}/analysis")
async def get_analysis(project_id: int, current_user: CurrentUser, db: DBSession):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.analysis_result or {}
