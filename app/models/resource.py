from pydantic import BaseModel, Field


class Resource(BaseModel):
    """실행 중 AWS 인스턴스 리소스 사용량 정보를 나타냅니다."""

    timestamp_ms: int = Field(..., description="타임스탬프(밀리초)")
    cpu_percent: float = Field(..., description="총 CPU 사용률(%)")
    memory_total_mb: float = Field(..., description="총 메모리(MB)")
    memory_used_mb: float = Field(..., description="총 사용 중 메모리(MB)")
    memory_percent: float = Field(..., description="총 메모리 사용률(%)")

    class Config:
        json_encoders = {
            int: lambda v: v,
            float: lambda v: v,
        }

class ResourceResponse(BaseModel):
    """시스템 리소스 사용량 응답 스키마입니다."""

    timestamp_ms: int = Field(..., description="타임스탬프(밀리초)")
    cpu_percent: float = Field(..., description="총 CPU 사용률(%)")
    memory_total_mb: float = Field(..., description="총 메모리(MB)")
    memory_used_mb: float = Field(..., description="총 사용 중 메모리(MB)")
    memory_percent: float = Field(..., description="총 메모리 사용률(%)")
