from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from config.settings import settings
from config.db import init_db

# ORM 엔티티 임포트 (Base.metadata에 등록하기 위해)
from app.schemas.project import ProjectORM
from app.schemas.job import JobORM
from app.schemas.execution import ExecutionORM
from app.schemas.log import LogORM

# 애플리케이션 시작 시 테이블 생성
init_db()

app = FastAPI(
    title="서비스 서버 - 코드 실행 관리자",
    description="코드 업로드/실행 요청을 관리하는 API 게이트웨이",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["execution"])


@app.get("/")
async def root() -> dict:
    """서비스 메타 정보를 반환합니다.

    Returns:
        서비스 이름, 버전, 상태가 포함된 딕셔너리.
    """
    return {
        "service": "서비스 서버 - 코드 실행 관리자",
        "version": "0.1.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
