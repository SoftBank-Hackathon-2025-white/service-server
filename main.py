from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from config.settings import settings

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
    """서비스 메타 정보를 반환합니다."""
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
