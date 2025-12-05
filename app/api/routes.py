from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from app.models.code import CodeUploadRequest
from app.models.job import JobResponse, JobStatus
from app.models.execution import ExecutionRequest
from app.services.job_service import JobService
from app.services.execution_service import ExecutionService
from app.services.s3_service import S3Service


router = APIRouter()

job_service = JobService()
execution_service = ExecutionService()
s3_service = S3Service()


async def run_execution_and_update_job(job_id: str, execution_request: ExecutionRequest) -> None:
    """Execution Engine 실행 후 Job 상태와 결과를 갱신하는 백그라운드 작업입니다.

    Args:
        job_id: 실행 대상 Job ID.
        execution_request: Execution Engine에 전달할 실행 요청 정보.
    """
    try:
        result = await execution_service.submit_execution(execution_request)

        if result:
            job_service.update_job_status(job_id, JobStatus.SUCCESS)
            job_service.update_job_result(job_id, result)
        else:
            job_service.update_job_status(job_id, JobStatus.FAILED)
    except Exception:
        job_service.update_job_status(job_id, JobStatus.FAILED)


@router.post("/upload", response_model=JobResponse)
async def upload_code(code_request: CodeUploadRequest) -> JobResponse:
    """사용자 코드를 업로드하고 새로운 Job을 생성합니다.

    Args:
        code_request: 업로드할 코드와 언어 정보.

    Returns:
        생성된 Job 정보가 담긴 응답 객체.
    """
    
    if code_request.language not in ("python", "node"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {code_request.language}"
        )
    
    try:
        code_key = await s3_service.upload_user_code(
            code=code_request.code,
            language=code_request.language
        )
        if not code_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload code to storage"
            )

        job = job_service.create_job(code_request, code_key)

        response = job_service.to_response(job, "Code uploaded successfully")
        return JobResponse(**response.dict())
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload code"
        )


@router.post("/execute/{job_id}", response_model=JobResponse)
async def execute_code(
    job_id: str,
    background_tasks: BackgroundTasks,
    input_data: str = ""
) -> JobResponse:
    """기존 Job에 대해 코드 실행을 비동기로 트리거합니다.

    Args:
        job_id: 실행할 Job ID.
        background_tasks: FastAPI 백그라운드 작업 객체.
        input_data: 실행 시 전달할 표준 입력 데이터.

    Returns:
        실행이 트리거된 Job 정보 응답.
    """
    try:
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        job_service.update_job_status(job_id, JobStatus.RUNNING)

        execution_request = ExecutionRequest(
            job_id=job_id,
            code_key=job.code_key,
            language=job.language,
            input=input_data,
            timeout=job.timeout_ms
        )

        if background_tasks is not None:
            background_tasks.add_task(run_execution_and_update_job, job_id, execution_request)
        else:
            import asyncio
            asyncio.create_task(run_execution_and_update_job(job_id, execution_request))

        job = job_service.get_job(job_id) or job
        return job_service.to_response(job, "Execution started")

    except HTTPException:
        raise
    except Exception:
        job_service.update_job_status(job_id, JobStatus.FAILED)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger execution"
        )


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(limit: int = 100) -> list[JobResponse]:
    """Job 목록을 페이지 없이 전체 조회합니다.

    Args:
        limit: 최대 조회 개수.

    Returns:
        Job 응답 객체 리스트.
    """
    try:
        jobs = job_service.list_jobs(limit=limit)
        return [job_service.to_response(j) for j in jobs]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs"
        )


@router.get("/health")
async def health_check() -> dict:
    """서비스 헬스 체크 정보를 반환합니다.

    Returns:
        서비스 상태와 환경 정보 딕셔너리.
    """
    return {
        "status": "healthy",
        "environment": "service-server"
    }
