from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    file_path: Optional[str] = None
    context_type: Optional[str] = "project"


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_id: int
    role: str
    content: str
    file_path: Optional[str]
    tokens_used: int
    provider: Optional[str]
    created_at: datetime


class AIExplainRequest(BaseModel):
    file_path: str
    code: Optional[str] = None


class AIExplainResponse(BaseModel):
    purpose: str
    business_logic: str
    inputs: list[str]
    outputs: list[str]
    complexity: str
    dependencies: list[str]


class AIRefactorRequest(BaseModel):
    file_path: str
    code: str
    refactor_type: str = Field(..., description="rename, extract_method, performance, solid, clean_code, security, async")


class AIRefactorResponse(BaseModel):
    original_code: str
    refactored_code: str
    changes_summary: str
    suggestions: list[str]


class AIBugDetectionRequest(BaseModel):
    file_path: str
    code: str


class AIBugDetectionResponse(BaseModel):
    issues: list[dict[str, Any]]
    severity_summary: dict[str, int]
    recommendations: list[str]


class TestGenerateRequest(BaseModel):
    file_paths: list[str] = []
    test_framework: str = "pytest"
    include_integration: bool = False
    include_api_tests: bool = True


class DocumentationRequest(BaseModel):
    doc_types: list[str] = Field(default=["readme", "api", "architecture"])
    format: str = "markdown"


class AIProviderConfig(BaseModel):
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None


class AIUsageResponse(BaseModel):
    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    cost: float
    operation: str
    created_at: datetime
