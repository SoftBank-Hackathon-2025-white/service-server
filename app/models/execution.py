from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ExecutionRequest(BaseModel):
    """Execution Engine으로 전달하는 실행 요청 스키마입니다."""

    job_id: str = Field(..., description="고유 Job ID")
    code_key: str = Field(..., description="실행할 S3 코드 키")
    language: str = Field(..., description="프로그래밍 언어")
    input: Optional[str] = Field("", description="코드 입력 데이터")
    timeout: int = Field(default=5000, description="타임아웃(밀리초)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abcd-1234",
                "language": "python",
                "code_key": "python/550e8400-e29b-41d4-a716-446655440000",
                "input": "",
                "timeout": 5000,
            }
        }


class ResourceMetrics(BaseModel):
    """실행 시 리소스 사용량 메트릭입니다."""

    cpu_percent: float = Field(..., description="CPU 사용률(%)")
    memory_mb: float = Field(..., description="메모리 사용량(MB)")
    execution_time_ms: float = Field(..., description="실행 소요 시간(ms)")


class ExecutionResult(BaseModel):
    """Execution Engine이 반환하는 실행 결과 스키마입니다."""

    job_id: str = Field(..., description="고유 Job ID")
    status: str = Field(..., description="실행 상태")
    stdout: str = Field(default="", description="표준 출력")
    stderr: str = Field(default="", description="표준 에러")
    resource: Optional[ResourceMetrics] = Field(None, description="리소스 사용량")
    code_key: Optional[str] = Field(None, description="실행한 코드 S3 키")
    log_key: Optional[str] = Field(None, description="로그 파일 식별자")
    logs_url: Optional[str] = Field(None, description="실행 로그 S3 URL")
    error_message: Optional[str] = Field(None, description="실패 시 에러 메시지")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="완료 시각")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
