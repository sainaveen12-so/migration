from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import (
    AIResponse,
    AIUsage,
    AuditLog,
    ChatMessage,
    JobStatus,
    MigrationJob,
    Notification,
)


class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> MigrationJob:
        job = MigrationJob(**kwargs)
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def get_by_id(self, job_id: int) -> Optional[MigrationJob]:
        result = await self.db.execute(select(MigrationJob).where(MigrationJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_by_celery_id(self, celery_task_id: str) -> Optional[MigrationJob]:
        result = await self.db.execute(select(MigrationJob).where(MigrationJob.celery_task_id == celery_task_id))
        return result.scalar_one_or_none()

    async def update(self, job: MigrationJob, **kwargs) -> MigrationJob:
        for key, value in kwargs.items():
            if value is not None and hasattr(job, key):
                setattr(job, key, value)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def get_by_project(self, project_id: int) -> list[MigrationJob]:
        result = await self.db.execute(
            select(MigrationJob)
            .where(MigrationJob.project_id == project_id)
            .order_by(MigrationJob.created_at.desc())
        )
        return list(result.scalars().all())


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> ChatMessage:
        message = ChatMessage(**kwargs)
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_by_project(self, project_id: int, limit: int = 100) -> list[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.project_id == project_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class AIUsageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> AIUsage:
        usage = AIUsage(**kwargs)
        self.db.add(usage)
        await self.db.flush()
        return usage

    async def get_stats(self, user_id: int) -> dict:
        result = await self.db.execute(
            select(
                func.count(AIUsage.id),
                func.coalesce(func.sum(AIUsage.tokens_input + AIUsage.tokens_output), 0),
                func.coalesce(func.sum(AIUsage.cost), 0.0),
            ).where(AIUsage.user_id == user_id)
        )
        row = result.one()
        return {"count": row[0], "total_tokens": row[1], "total_cost": float(row[2])}

    async def save_response(self, **kwargs) -> AIResponse:
        response = AIResponse(**kwargs)
        self.db.add(response)
        await self.db.flush()
        return response


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Notification:
        notification = Notification(**kwargs)
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def get_by_user(self, user_id: int, unread_only: bool = False, limit: int = 50) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        result = await self.db.execute(query.order_by(Notification.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def mark_read(self, notification_id: int, user_id: int) -> None:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        )
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_read = True
            await self.db.flush()


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, action: str, resource_type: str, user_id: int | None = None, resource_id: int | None = None, details: dict | None = None, ip_address: str | None = None) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(log)
        await self.db.flush()
        return log
