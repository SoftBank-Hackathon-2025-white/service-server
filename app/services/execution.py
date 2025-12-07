import ast
import httpx
from typing import Optional, Dict, Any
from app.models.execution import ExecutionRequest, ExecutionResult, ResourceMetrics
from app.schemas.execution import ExecutionORM
from app.schemas.job import JobORM
from config.settings import settings
from sqlalchemy.orm import Session
from datetime import datetime
import uuid


class ExecutionService:
    """코드 실행 요청을 위임하고 Execution Engine과 통신하는 서비스입니다."""

    def __init__(self, db: Session) -> None:
        """엔진 URL과 타임아웃, 데이터베이스 세션을 초기화합니다."""
        self.engine_url = settings.EXECUTION_ENGINE_URL
        self.timeout = settings.EXECUTION_ENGINE_TIMEOUT / 1000
        self.db = db

    async def submit_execution(self, execution_request: ExecutionRequest) -> Optional[ExecutionResult]:
        """Execution Engine으로 코드 실행을 트리거하고 결과를 저장합니다.

        Args:
            execution_request: 실행할 Job과 코드 키, 언어 정보.

        Returns:
            저장된 ExecutionResult DTO 또는 실패 시 None.
        """
        try:
            lang = execution_request.language.lower()

            if lang not in ("python", "node", "java"):  
                return None

            run_url = {
                "java": settings.EXECUTION_ENGINE_JAVA_RUN_URL,
                "python": settings.EXECUTION_ENGINE_PYTHON_RUN_URL, 
                "node": settings.EXECUTION_ENGINE_NODE_RUN_URL
            }[lang]
                
            params = {"code_key": execution_request.code_key}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(run_url, params=params)

                if response.status_code != 200:
                    return None
                
                text = response.text.strip()
                print(f"[DEBUG] Execution Engine 응답: {text}")  # 디버그 로그

                if text.startswith("{") and text.endswith("}"):
                    data = ast.literal_eval(text)
                    if isinstance(data, dict):
                        execution_orm = ExecutionORM(
                            execution_id=str(uuid.uuid4()),
                            job_id=execution_request.job_id,
                            stdout=data.get("stdout", ""),
                            stderr=data.get("stderr", ""),
                            code_key=data.get("code_key"),
                            log_key=data.get("log_key"),
                            logs_url=data.get("logs_url"),
                            cpu_percent=data.get("cpu_percent"),
                            memory_mb=data.get("memory_mb"),
                            execution_time_ms=data.get("execution_time_ms"),
                            completed_at=datetime.utcnow()
                        )
                        self.db.add(execution_orm)
                        self.db.commit()
                        
                        return self._orm_to_dto(execution_orm)

        except httpx.TimeoutException:
            return None
        except Exception:
            return None

    async def get_execution_status(self, job_id: str) -> Optional[dict]:
        """데이터베이스에서 Job의 가장 최근 Execution 결과를 조회합니다.

        Args:
            job_id: 조회할 Job ID.

        Returns:
            상태/결과 JSON 딕셔너리 또는 None.
        """
        try:
            execution_orm = self.db.query(ExecutionORM).filter(
                ExecutionORM.job_id == job_id
            ).order_by(ExecutionORM.completed_at.desc()).first()

            if execution_orm:
                result = self._orm_to_dto(execution_orm)
                return result.dict()

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
    
    def _orm_to_dto(self, execution_orm: ExecutionORM) -> ExecutionResult:
        """ExecutionORM을 ExecutionResult DTO로 변환합니다."""
        resource_metrics = None
        if (execution_orm.cpu_percent is not None or 
            execution_orm.memory_mb is not None or 
            execution_orm.execution_time_ms is not None):
            resource_metrics = ResourceMetrics(
                cpu_percent=execution_orm.cpu_percent or 0.0,
                memory_mb=execution_orm.memory_mb or 0.0,
                execution_time_ms=execution_orm.execution_time_ms or 0.0
            )
        
        return ExecutionResult(
            job_id=execution_orm.job_id,
            status="COMPLETED",
            stdout=execution_orm.stdout,
            stderr=execution_orm.stderr,
            resource=resource_metrics,
            code_key=execution_orm.code_key,
            log_key=execution_orm.log_key,
            logs_url=execution_orm.logs_url,
            completed_at=execution_orm.completed_at
        )
