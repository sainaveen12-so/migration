from fastapi import APIRouter, HTTPException

from app.ai.factory import AIProviderFactory
from app.core.deps import CurrentUser, DBSession
from app.models.user import JobType
from app.repositories.job_repository import AIUsageRepository, ChatRepository, JobRepository, NotificationRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.ai import (
    AIBugDetectionRequest,
    AIBugDetectionResponse,
    AIExplainRequest,
    AIExplainResponse,
    AIProviderConfig,
    AIRefactorRequest,
    AIRefactorResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    DocumentationRequest,
    TestGenerateRequest,
)
from app.services.ai_service import AIService
from app.tasks.migration_tasks import generate_documentation_task, generate_tests_task

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/providers")
async def list_providers():
    return {
        "providers": AIProviderFactory.list_providers(),
        "current": AIProviderFactory.get_current_provider_name(),
    }


@router.post("/providers/switch")
async def switch_provider(config: AIProviderConfig, current_user: CurrentUser):
    try:
        AIProviderFactory.set_default_provider(config.provider)
        provider = AIProviderFactory.get_provider(config.provider, model=config.model)
        return {"provider": provider.provider_name, "model": getattr(provider, "model", config.model)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/chat", response_model=ChatMessageResponse)
async def chat(project_id: int, data: ChatMessageCreate, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chat_repo = ChatRepository(db)
    await chat_repo.create(
        project_id=project_id, user_id=current_user.id, role="user", content=data.content, file_path=data.file_path
    )

    history = await chat_repo.get_by_project(project_id)
    messages = [{"role": m.role, "content": m.content} for m in history[-20:]]

    context = str(project.analysis_result or {})[:4000]
    if data.file_path:
        file = await project_repo.get_file_by_path(project_id, data.file_path)
        if file and file.content:
            context += f"\n\nFile {data.file_path}:\n{file.content[:3000]}"

    ai_svc = AIService()
    result = await ai_svc.chat(messages, context)

    usage_repo = AIUsageRepository(db)
    await usage_repo.create(
        user_id=current_user.id,
        project_id=project_id,
        provider=result["provider"],
        model=result["model"],
        tokens_input=result["tokens_input"],
        tokens_output=result["tokens_output"],
        cost=result["cost"],
        operation="chat",
    )

    response_msg = await chat_repo.create(
        project_id=project_id,
        user_id=current_user.id,
        role="assistant",
        content=result["content"],
        tokens_used=result["tokens_input"] + result["tokens_output"],
        provider=result["provider"],
    )
    return response_msg


@router.get("/projects/{project_id}/chat", response_model=list[ChatMessageResponse])
async def get_chat_history(project_id: int, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await ChatRepository(db).get_by_project(project_id)


@router.post("/projects/{project_id}/explain", response_model=AIExplainResponse)
async def explain_code(project_id: int, data: AIExplainRequest, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    code = data.code
    if not code:
        file = await project_repo.get_file_by_path(project_id, data.file_path)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        code = file.content or ""

    ai_svc = AIService()
    result = await ai_svc.explain_code(code, data.file_path)
    return AIExplainResponse(
        purpose=result.get("purpose", ""),
        business_logic=result.get("business_logic", ""),
        inputs=result.get("inputs", []),
        outputs=result.get("outputs", []),
        complexity=result.get("complexity", "unknown"),
        dependencies=result.get("dependencies", []),
    )


@router.post("/projects/{project_id}/refactor", response_model=AIRefactorResponse)
async def refactor_code(project_id: int, data: AIRefactorRequest, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ai_svc = AIService()
    result = await ai_svc.refactor_code(data.code, data.refactor_type, data.file_path)
    return AIRefactorResponse(**result)


@router.post("/projects/{project_id}/bugs", response_model=AIBugDetectionResponse)
async def detect_bugs(project_id: int, data: AIBugDetectionRequest, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ai_svc = AIService()
    result = await ai_svc.detect_bugs(data.code, data.file_path)
    return AIBugDetectionResponse(
        issues=result.get("issues", []),
        severity_summary=result.get("severity_summary", {}),
        recommendations=result.get("recommendations", []),
    )


@router.post("/projects/{project_id}/generate-tests")
async def generate_tests(project_id: int, data: TestGenerateRequest, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job_repo = JobRepository(db)
    job = await job_repo.create(project_id=project_id, job_type=JobType.TESTING)
    task = generate_tests_task.delay(project_id, job.id, data.file_paths, data.test_framework)
    await job_repo.update(job, celery_task_id=task.id)
    return {"job_id": job.id, "task_id": task.id, "status": "started"}


@router.post("/projects/{project_id}/generate-docs")
async def generate_docs(project_id: int, data: DocumentationRequest, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job_repo = JobRepository(db)
    job = await job_repo.create(project_id=project_id, job_type=JobType.DOCUMENTATION)
    task = generate_documentation_task.delay(project_id, job.id, data.doc_types)
    await job_repo.update(job, celery_task_id=task.id)
    return {"job_id": job.id, "task_id": task.id, "status": "started"}


@router.get("/projects/{project_id}/diagrams")
async def get_diagrams(project_id: int, current_user: CurrentUser, db: DBSession):
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ai_svc = AIService()
    return await ai_svc.generate_diagrams(project.analysis_result or {})
