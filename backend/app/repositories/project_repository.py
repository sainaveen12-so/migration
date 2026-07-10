from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Project, ProjectFile, ProjectStatus, ProjectVersion


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: int, owner_id: int | None = None) -> Optional[Project]:
        query = select(Project).where(Project.id == project_id)
        if owner_id:
            query = query.where(Project.owner_id == owner_id)
        result = await self.db.execute(query.options(selectinload(Project.files)))
        return result.scalar_one_or_none()

    async def get_all(self, owner_id: int, skip: int = 0, limit: int = 50) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Project:
        project = Project(**kwargs)
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project, **kwargs) -> Project:
        for key, value in kwargs.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)

    async def count_by_owner(self, owner_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Project).where(Project.owner_id == owner_id)
        )
        return result.scalar() or 0

    async def count_by_status(self, owner_id: int) -> dict[str, int]:
        result = await self.db.execute(
            select(Project.status, func.count())
            .where(Project.owner_id == owner_id)
            .group_by(Project.status)
        )
        return {status.value: count for status, count in result.all()}

    async def get_recent(self, owner_id: int, limit: int = 5) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_file(self, project_id: int, **kwargs) -> ProjectFile:
        file = ProjectFile(project_id=project_id, **kwargs)
        self.db.add(file)
        await self.db.flush()
        await self.db.refresh(file)
        return file

    async def get_files(self, project_id: int) -> list[ProjectFile]:
        result = await self.db.execute(
            select(ProjectFile).where(ProjectFile.project_id == project_id).order_by(ProjectFile.file_path)
        )
        return list(result.scalars().all())

    async def get_file(self, project_id: int, file_id: int) -> Optional[ProjectFile]:
        result = await self.db.execute(
            select(ProjectFile).where(ProjectFile.project_id == project_id, ProjectFile.id == file_id)
        )
        return result.scalar_one_or_none()

    async def get_file_by_path(self, project_id: int, file_path: str) -> Optional[ProjectFile]:
        result = await self.db.execute(
            select(ProjectFile).where(ProjectFile.project_id == project_id, ProjectFile.file_path == file_path)
        )
        return result.scalar_one_or_none()

    async def create_version(self, project_id: int, version_number: int, **kwargs) -> ProjectVersion:
        version = ProjectVersion(project_id=project_id, version_number=version_number, **kwargs)
        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def get_versions(self, project_id: int) -> list[ProjectVersion]:
        result = await self.db.execute(
            select(ProjectVersion)
            .where(ProjectVersion.project_id == project_id)
            .order_by(ProjectVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def get_latest_version_number(self, project_id: int) -> int:
        result = await self.db.execute(
            select(func.max(ProjectVersion.version_number)).where(ProjectVersion.project_id == project_id)
        )
        return result.scalar() or 0

    async def search_files(self, owner_id: int, query: str, limit: int = 50) -> list[ProjectFile]:
        pattern = f"%{query}%"
        result = await self.db.execute(
            select(ProjectFile)
            .join(Project)
            .where(
                Project.owner_id == owner_id,
                (ProjectFile.file_name.ilike(pattern) | ProjectFile.file_path.ilike(pattern) | ProjectFile.content.ilike(pattern)),
            )
            .limit(limit)
        )
        return list(result.scalars().all())
