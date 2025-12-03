import httpx
from typing import Optional, Dict, Any
from app.models.execution import ExecutionRequest
from config.settings import settings


class ExecutionService:
    """코드 실행 요청을 위임하고 Execution Engine과 통신합니다."""

    def __init__(self) -> None:
        """엔진 URL과 타임아웃을 초기화합니다."""
        self.engine_url = settings.EXECUTION_ENGINE_URL
        self.timeout = settings.EXECUTION_ENGINE_TIMEOUT / 1000

    async def submit_execution(self, execution_request: ExecutionRequest) -> Optional[Dict[str, Any]]:
        """Execution Engine으로 코드 실행을 트리거하고 결과를 반환합니다.

        Returns:
            엔진 응답 JSON 또는 실패 시 None.
        """
        try:
            run_url = settings.EXECUTION_ENGINE_PYTHON_RUN_URL
            if execution_request.language.lower() == "node":
                run_url = settings.EXECUTION_ENGINE_NODE_RUN_URL
            elif execution_request.language.lower() not in ("python", "node"):
                run_url = f"{settings.EXECUTION_ENGINE_BASE_URL}/{execution_request.language}/run"

            params = {"code_key": execution_request.code}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(run_url, params=params)
                if response.status_code in (200, 202):
                    return response.json()
                return None

        except httpx.TimeoutException:
            return None
        except Exception:
            return None

    async def get_execution_status(self, job_id: str) -> Optional[dict]:
        """Execution Engine에서 실행 상태/결과를 조회합니다."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.engine_url}/status/{job_id}",
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    return response.json()

                return None

        except Exception:
            return None

    async def cancel_execution(self, job_id: str) -> bool:
        """진행 중인 실행을 취소합니다."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.engine_url}/cancel/{job_id}",
                    headers={"Content-Type": "application/json"}
                )

                return response.status_code == 200

        except Exception:
            return False
