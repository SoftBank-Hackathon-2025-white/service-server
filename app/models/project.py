from pydantic import BaseModel, Field
from typing import Optional


class ProjectResponse(BaseModel):
    """프로젝트 응답 스키마입니다."""

    project_id: int = Field(..., description="프로젝트 고유 ID")
    project: str = Field(..., description="프로젝트 이름")
    description: Optional[str] = Field(None, description="프로젝트 설명")

    class Config:
        from_attributes = True
