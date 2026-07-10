from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    source_framework: Optional[str] = None
    target_framework: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_language: Optional[str] = None
    target_framework: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    source_language: Optional[str]
    target_language: Optional[str]
    source_framework: Optional[str]
    target_framework: Optional[str]
    status: str
    total_files: int
    total_lines: int
    complexity_score: Optional[float]
    owner_id: int
    github_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class ProjectFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    file_path: str
    file_name: str
    language: Optional[str]
    lines_of_code: int
    complexity: Optional[float]
    file_type: Optional[str]
    created_at: datetime


class ProjectFileContentResponse(ProjectFileResponse):
    content: Optional[str]
    migrated_content: Optional[str]


class GitHubCloneRequest(BaseModel):
    github_url: str
    name: Optional[str] = None
    branch: str = "main"


class MigrationRequest(BaseModel):
    target_language: str
    target_framework: Optional[str] = None
    migration_type: str


class AnalysisResult(BaseModel):
    language: Optional[str]
    framework: Optional[str]
    dependencies: list[str] = []
    folder_structure: dict[str, Any] = {}
    rest_apis: list[dict[str, Any]] = []
    database: Optional[dict[str, Any]] = None
    orm: Optional[str] = None
    controllers: list[str] = []
    services: list[str] = []
    repositories: list[str] = []
    utilities: list[str] = []
    summary: Optional[str] = None
    complexity_report: Optional[dict[str, Any]] = None
    architecture_overview: Optional[str] = None


class ProjectVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    version_number: int
    description: Optional[str]
    changes_summary: Optional[dict[str, Any]]
    created_at: datetime
