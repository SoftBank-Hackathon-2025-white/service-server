from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


class JobStatus(str, Enum):
    """Job 실행 상태 열거형입니다."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


class Job(BaseModel):
    """코드 실행 Job을 표현하는 모델입니다."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="고유 Job ID")
    project: str = Field(..., description="프로젝트 이름")
    code_key: str = Field(..., description="실행할 S3 코드 키")
    language: str = Field(..., description="프로그래밍 언어")
    status: JobStatus = Field(default=JobStatus.PENDING, description="현재 상태")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시각")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="최종 갱신 시각")
    started_at: Optional[datetime] = Field(None, description="실행 시작 시각")
    completed_at: Optional[datetime] = Field(None, description="실행 완료 시각")
    timeout_ms: int = Field(default=5000, description="타임아웃(밀리초)")
    result: Optional[Dict[str, Any]] = Field(default=None, description="실행 결과(stdout, stderr, logs_url 등)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JobResponse(BaseModel):
    """API 응답에 사용되는 Job 응답 스키마입니다."""

    job_id: str = Field(..., description="고유 Job ID")
    project: str = Field(..., description="프로젝트 이름")
    code_key: str = Field(..., description="실행할 S3 코드 키")
    status: JobStatus = Field(..., description="현재 상태")
    message: str = Field(..., description="상태 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="추가 데이터")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
