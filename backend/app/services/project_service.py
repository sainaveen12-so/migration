import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.config import settings
from app.models.user import ProjectFile, ProjectStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.job_repository import AIUsageRepository, AuditRepository, NotificationRepository
from app.services.analysis_service import FileExtractor, ProjectAnalyzer
from app.services.migration_service import MigrationService


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        audit_repo: AuditRepository | None = None,
        notification_repo: NotificationRepository | None = None,
    ):
        self.project_repo = project_repo
        self.audit_repo = audit_repo
        self.notification_repo = notification_repo
        self.analyzer = ProjectAnalyzer()
        self.extractor = FileExtractor()

    async def create_project(self, owner_id: int, **kwargs):
        project = await self.project_repo.create(owner_id=owner_id, **kwargs)
        if self.audit_repo:
            await self.audit_repo.log("create", "project", owner_id, project.id, {"name": project.name})
        return project

    async def upload_zip(self, project_id: int, owner_id: int, file_content: bytes, filename: str) -> dict:
        project = await self.project_repo.get_by_id(project_id, owner_id)
        if not project:
            raise ValueError("Project not found")

        upload_dir = os.path.join(settings.UPLOAD_DIR, str(project_id), str(uuid.uuid4()))
        os.makedirs(upload_dir, exist_ok=True)

        zip_path = os.path.join(upload_dir, filename)
        with open(zip_path, "wb") as f:
            f.write(file_content)

        extract_dir = os.path.join(upload_dir, "source")
        self.extractor.extract_zip(zip_path, extract_dir)
        project_root = self.extractor.get_project_root(extract_dir)

        await self.project_repo.update(project, source_path=project_root, status=ProjectStatus.PENDING)
        return {"project_id": project_id, "source_path": project_root, "status": "uploaded"}

    async def analyze_project(self, project_id: int, owner_id: int) -> dict:
        project = await self.project_repo.get_by_id(project_id, owner_id)
        if not project or not project.source_path:
            raise ValueError("Project not found or no source uploaded")

        await self.project_repo.update(project, status=ProjectStatus.ANALYZING)
        analysis = self.analyzer.analyze_project(project.source_path)

        for file_info in analysis.get("files", []):
            await self.project_repo.add_file(
                project_id=project_id,
                file_path=file_info["path"],
                file_name=file_info["name"],
                language=file_info.get("language"),
                content=file_info.get("content", "")[:50000],
                lines_of_code=file_info.get("lines", 0),
                file_type=file_info.get("extension"),
            )

        files_for_storage = analysis.pop("files", [])
        await self.project_repo.update(
            project,
            status=ProjectStatus.ANALYZED,
            source_language=analysis.get("language"),
            source_framework=analysis.get("framework"),
            analysis_result=analysis,
            complexity_score=analysis.get("complexity_score"),
            total_files=analysis.get("total_files", 0),
            total_lines=analysis.get("total_lines", 0),
        )

        if self.notification_repo:
            await self.notification_repo.create(
                user_id=owner_id,
                title="Analysis Complete",
                message=f"Project '{project.name}' analysis completed.",
                notification_type="analysis_completed",
                metadata_json={"project_id": project_id},
            )

        return analysis

    async def delete_project(self, project_id: int, owner_id: int) -> None:
        project = await self.project_repo.get_by_id(project_id, owner_id)
        if not project:
            raise ValueError("Project not found")

        if project.source_path and os.path.exists(project.source_path):
            import shutil
            parent = os.path.dirname(project.source_path)
            if os.path.exists(parent):
                shutil.rmtree(parent, ignore_errors=True)

        await self.project_repo.delete(project)
        if self.audit_repo:
            await self.audit_repo.log("delete", "project", owner_id, project_id)

    async def get_dashboard_stats(self, owner_id: int) -> dict:
        total_projects = await self.project_repo.count_by_owner(owner_id)
        status_counts = await self.project_repo.count_by_status(owner_id)
        recent = await self.project_repo.get_recent(owner_id, 5)

        from app.models.user import Project

        files_result = await self.project_repo.db.execute(
            select(func.count(ProjectFile.id), func.coalesce(func.sum(ProjectFile.lines_of_code), 0))
            .join(Project)
            .where(Project.owner_id == owner_id)
        )
        file_stats = files_result.one()

        return {
            "total_projects": total_projects,
            "total_files": file_stats[0] or 0,
            "total_lines_of_code": file_stats[1] or 0,
            "migration_status": status_counts,
            "recent_projects": [
                {"id": p.id, "name": p.name, "status": p.status.value, "updated_at": p.updated_at.isoformat()}
                for p in recent
            ],
        }
