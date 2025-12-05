import ast
import httpx
from typing import Optional, Dict, Any
from app.models.execution import ExecutionRequest
from config.settings import settings


class ExecutionService:
    """코드 실행 요청을 위임하고 Execution Engine과 통신하는 서비스입니다."""

    def __init__(self) -> None:
        """엔진 URL과 타임아웃을 초기화합니다."""
        self.engine_url = settings.EXECUTION_ENGINE_URL
        self.timeout = settings.EXECUTION_ENGINE_TIMEOUT / 1000

    async def submit_execution(self, execution_request: ExecutionRequest) -> Optional[Dict[str, Any]]:
        """Execution Engine으로 코드 실행을 트리거하고 결과를 반환합니다.

        Args:
            execution_request: 실행할 Job과 코드 키, 언어 정보.

        Returns:
            엔진 응답 딕셔너리 또는 실패 시 None.
        """
        try:
            lang = execution_request.language.lower()

            if lang not in ("python", "node"):
                return None

            run_url = (
                settings.EXECUTION_ENGINE_PYTHON_RUN_URL 
                if lang == "python" 
                else settings.EXECUTION_ENGINE_NODE_RUN_URL
            )
            params = {"code_key": execution_request.code_key}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(run_url, params=params)

                if response.status_code != 200:
                    return None
                
                text = response.text.strip()

                if text.startswith("{") and text.endswith("}"):
                    data = ast.literal_eval(text)
                    if isinstance(data, dict):
                        return data

        except httpx.TimeoutException:
            return None
        except Exception:
            return None

    async def get_execution_status(self, job_id: str) -> Optional[dict]:
        """Execution Engine에서 실행 상태와 결과를 조회합니다.

        Args:
            job_id: 조회할 Job ID.

        Returns:
            상태/결과 JSON 딕셔너리 또는 None.
        """
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
        """진행 중인 실행을 취소합니다.

        Args:
            job_id: 취소할 Job ID.

        Returns:
            취소 성공 여부.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.engine_url}/cancel/{job_id}",
                    headers={"Content-Type": "application/json"}
                )

                return response.status_code == 200

        except Exception:
            return False
