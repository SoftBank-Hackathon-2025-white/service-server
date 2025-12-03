import httpx
from typing import Optional, Dict, Any
from config.settings import settings


class ExecutionEngineClient:
    """Execution Engine와 통신하는 HTTP 클라이언트입니다.

    코드 실행, 상태 조회, 실행 취소 요청을 전달합니다.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None) -> None:
        """기본 URL과 타임아웃을 설정합니다.

        Args:
            base_url: Execution Engine 기본 URL.
            timeout: 요청 타임아웃(초).
        """
        self.base_url = base_url or settings.EXECUTION_ENGINE_URL
        self.timeout = timeout or (settings.EXECUTION_ENGINE_TIMEOUT / 1000)
    
    async def execute_code(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """코드 실행 요청을 전송합니다.

        Args:
            payload: 실행 요청 페이로드.
            
        Returns:
            응답 JSON 또는 실패 시 None.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/execute",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            return None
    
    async def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Execution Engine에서 실행 상태를 조회합니다.

        Args:
            job_id: 조회할 Job ID.
            
        Returns:
            상태 정보 딕셔너리 또는 실패 시 None.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/status/{job_id}")
                response.raise_for_status()
                return response.json()
        except Exception:
            return None
    
    async def cancel(self, job_id: str) -> bool:
        """진행 중인 실행을 취소합니다.

        Args:
            job_id: 취소할 Job ID.
            
        Returns:
            취소 성공 시 True, 실패 시 False.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/cancel/{job_id}")
                response.raise_for_status()
                return True
        except Exception:
            return False
