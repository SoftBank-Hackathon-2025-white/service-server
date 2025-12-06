from pydantic import BaseModel, Field
from typing import Optional, Literal


class CodeUploadRequest(BaseModel):
    """코드 업로드 요청 스키마입니다."""

    project: str = Field(..., description="프로젝트 이름")
    code: str = Field(..., description="사용자 소스 코드")
    language: Literal["python", "node", "java"] = Field(..., description="프로그래밍 언어")
    function_name: Optional[str] = Field(None, description="실행할 함수 이름(선택)")
    description: Optional[str] = Field(None, description="코드 설명")
    
    
    class Config:
        json_schema_extra = {
            "example": {
                "project": "my_project",
                "code": "def hello(name):\n    return f'Hello, {name}!'",
                "language": "python",
                "function_name": "hello",
                "description": "간단한 인사 함수",
            }
        }
