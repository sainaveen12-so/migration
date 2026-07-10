from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class DashboardStats(BaseModel):
    total_projects: int
    total_files: int
    total_lines_of_code: int
    migration_status: dict[str, int]
    ai_usage_count: int
    total_tokens: int
    total_cost: float
    recent_projects: list[dict[str, Any]]


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    job_type: str
    status: str
    progress: int
    celery_task_id: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    metadata_json: Optional[dict[str, Any]]
    created_at: datetime


class SearchResult(BaseModel):
    type: str
    id: int
    name: str
    path: Optional[str]
    project_id: Optional[int]
    project_name: Optional[str]
    snippet: Optional[str]
    score: float = 1.0


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: str
    celery: str
