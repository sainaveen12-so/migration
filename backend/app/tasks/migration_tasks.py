import asyncio
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.factory import AIProviderFactory
from app.core.config import settings
from app.core.database import get_sync_engine_kwargs
from app.models.user import JobStatus, JobType, ProjectStatus
from app.services.analysis_service import ProjectAnalyzer
from app.services.migration_service import MigrationService
from app.tasks.celery_app import celery_app


def get_sync_session():
    engine = create_engine(settings.DATABASE_URL_SYNC, **get_sync_engine_kwargs(settings.DATABASE_URL_SYNC))
    Session = sessionmaker(bind=engine)
    return Session()


@celery_app.task(bind=True, name="tasks.analyze_project")
def analyze_project_task(self, project_id: int, job_id: int, owner_id: int):
    session = get_sync_session()
    try:
        from app.models.user import MigrationJob, Project, ProjectFile

        job = session.query(MigrationJob).get(job_id)
        project = session.query(Project).get(project_id)
        if not job or not project:
            return {"error": "Job or project not found"}

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        job.celery_task_id = self.request.id
        session.commit()

        analyzer = ProjectAnalyzer()
        analysis = analyzer.analyze_project(project.source_path)

        for file_info in analysis.get("files", []):
            pf = ProjectFile(
                project_id=project_id,
                file_path=file_info["path"],
                file_name=file_info["name"],
                language=file_info.get("language"),
                content=file_info.get("content", "")[:50000],
                lines_of_code=file_info.get("lines", 0),
                file_type=file_info.get("extension"),
            )
            session.add(pf)

        files_data = analysis.pop("files", [])
        project.status = ProjectStatus.ANALYZED
        project.source_language = analysis.get("language")
        project.source_framework = analysis.get("framework")
        project.analysis_result = analysis
        project.complexity_score = analysis.get("complexity_score")
        project.total_files = analysis.get("total_files", 0)
        project.total_lines = analysis.get("total_lines", 0)

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.result = {"analysis": analysis}
        job.completed_at = datetime.now(timezone.utc)
        session.commit()

        return {"status": "completed", "project_id": project_id}
    except Exception as e:
        session.rollback()
        job = session.query(MigrationJob).get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            session.commit()
        raise
    finally:
        session.close()


@celery_app.task(bind=True, name="tasks.migrate_project")
def migrate_project_task(self, project_id: int, job_id: int, target_language: str, target_framework: str | None):
    session = get_sync_session()
    try:
        from app.models.user import MigrationJob, Notification, Project

        job = session.query(MigrationJob).get(job_id)
        project = session.query(Project).get(project_id)
        if not job or not project:
            return {"error": "Not found"}

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        job.celery_task_id = self.request.id
        project.status = ProjectStatus.MIGRATING
        session.commit()

        def update_progress(pct):
            job.progress = pct
            session.commit()
            self.update_state(state="PROGRESS", meta={"progress": pct})

        provider = AIProviderFactory.get_provider()
        migration_svc = MigrationService(provider)

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            migration_svc.migrate_project(
                project.source_path,
                target_language,
                target_framework,
                project.analysis_result or {},
                update_progress,
            )
        )
        loop.close()

        project.status = ProjectStatus.MIGRATED
        project.target_language = target_language
        project.target_framework = target_framework
        project.migrated_path = result["migrated_path"]

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.result = result
        job.completed_at = datetime.now(timezone.utc)

        notification = Notification(
            user_id=project.owner_id,
            title="Migration Completed",
            message=f"Project '{project.name}' migration completed successfully.",
            notification_type="migration_completed",
            metadata_json={"project_id": project_id},
        )
        session.add(notification)
        session.commit()

        return result
    except Exception as e:
        session.rollback()
        job = session.query(MigrationJob).get(job_id)
        project = session.query(Project).get(project_id)
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
        if project:
            project.status = ProjectStatus.FAILED
        session.commit()

        if project:
            notification = Notification(
                user_id=project.owner_id,
                title="Migration Failed",
                message=f"Project '{project.name}' migration failed: {str(e)[:200]}",
                notification_type="migration_failed",
                metadata_json={"project_id": project_id},
            )
            session.add(notification)
            session.commit()
        raise
    finally:
        session.close()


@celery_app.task(bind=True, name="tasks.generate_documentation")
def generate_documentation_task(self, project_id: int, job_id: int, doc_types: list[str]):
    session = get_sync_session()
    try:
        from app.models.user import MigrationJob, Notification, Project
        from app.services.ai_service import AIService

        job = session.query(MigrationJob).get(job_id)
        project = session.query(Project).get(project_id)
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        session.commit()

        ai_svc = AIService()
        summary = str(project.analysis_result or {})
        docs = {}

        loop = asyncio.new_event_loop()
        for i, doc_type in enumerate(doc_types):
            docs[doc_type] = loop.run_until_complete(ai_svc.generate_documentation(summary, doc_type))
            job.progress = int((i + 1) / len(doc_types) * 100)
            session.commit()
        loop.close()

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.result = {"documentation": docs}
        job.completed_at = datetime.now(timezone.utc)

        notification = Notification(
            user_id=project.owner_id,
            title="Documentation Generated",
            message=f"Documentation for '{project.name}' is ready.",
            notification_type="documentation_generated",
            metadata_json={"project_id": project_id},
        )
        session.add(notification)
        session.commit()
        return docs
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        session.commit()
        raise
    finally:
        session.close()


@celery_app.task(bind=True, name="tasks.generate_tests")
def generate_tests_task(self, project_id: int, job_id: int, file_paths: list[str], framework: str):
    session = get_sync_session()
    try:
        from app.models.user import MigrationJob, Notification, Project, ProjectFile
        from app.services.ai_service import AIService

        job = session.query(MigrationJob).get(job_id)
        project = session.query(Project).get(project_id)
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        session.commit()

        ai_svc = AIService()
        tests = {}
        files = session.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
        if file_paths:
            files = [f for f in files if f.file_path in file_paths]

        loop = asyncio.new_event_loop()
        for i, f in enumerate(files[:20]):
            if f.content:
                tests[f.file_path] = loop.run_until_complete(ai_svc.generate_tests(f.content, f.file_path, framework))
            job.progress = int((i + 1) / min(len(files), 20) * 100)
            session.commit()
        loop.close()

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.result = {"tests": tests}
        job.completed_at = datetime.now(timezone.utc)

        notification = Notification(
            user_id=project.owner_id,
            title="Tests Generated",
            message=f"Tests for '{project.name}' are ready.",
            notification_type="tests_generated",
            metadata_json={"project_id": project_id},
        )
        session.add(notification)
        session.commit()
        return tests
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        session.commit()
        raise
    finally:
        session.close()
