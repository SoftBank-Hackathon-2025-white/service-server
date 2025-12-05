from fastapi import APIRouter, HTTPException, status
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


@router.post("/upload", response_model=JobResponse)
async def upload_code(code_request: CodeUploadRequest) -> JobResponse:
    """코드를 업로드하고 Job을 생성합니다."""
    
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
async def execute_code(job_id: str, input_data: str = "") -> JobResponse:
    """코드 실행을 비동기로 트리거합니다."""
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

        result = await execution_service.submit_execution(execution_request)

        if result:
            job_service.update_job_status(job_id, JobStatus.SUCCESS)
            return JobResponse(
                job_id=job_id,
                status=JobStatus.SUCCESS,
                message="Execution completed",
                data={
                    "stdout": result.get("stdout"),
                    "stderr": result.get("stderr"),
                    "execution_time_ms": result.get("execution_time_ms"),
                    "cpu_percent ": result.get("cpu_percent"),
                    "memory_mb" : result.get("memory_mb"),
                    "logs_url": result.get("log_key") or result.get("logs_url"),
                    "code_key": job.code_key,
                }
            )

        job_service.update_job_status(job_id, JobStatus.FAILED)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Execution engine error for code_key={job.code_key}"
        )

    except HTTPException:
        raise
    except Exception:
        job_service.update_job_status(job_id, JobStatus.FAILED)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute code"
        )


@router.get("/status/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str) -> JobResponse:
    """현재 Job 상태를 조회하고 엔진 상태를 반영합니다."""
    try:
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        engine_status = await execution_service.get_execution_status(job_id)

        if engine_status:
            status_value = engine_status.get("status")
            mapped_status = job.status

            if status_value:
                try:
                    mapped_status = JobStatus(status_value)
                except ValueError:
                    mapped_status = job.status

            if mapped_status != job.status:
                job_service.update_job_status(job_id, mapped_status)
                job = job_service.get_job(job_id) or job

            return JobResponse(
                job_id=job_id,
                status=mapped_status,
                message=f"Job status: {mapped_status.value}",
                data={
                    "stdout": engine_status.get("stdout"),
                    "stderr": engine_status.get("stderr"),
                    "resource": engine_status.get("resource"),
                    "logs_url": engine_status.get("logs_url"),
                }
            )

        return job_service.to_response(job)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )


@router.post("/cancel/{job_id}", response_model=JobResponse)
async def cancel_job(job_id: str) -> JobResponse:
    """진행 중인 실행을 취소합니다."""
    try:
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        await execution_service.cancel_execution(job_id)

        job_service.update_job_status(job_id, JobStatus.CANCELLED)

        return job_service.to_response(job, "Job cancelled successfully")

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(limit: int = 100) -> list[JobResponse]:
    """모든 Job 목록을 조회합니다."""
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
    """서비스 상태를 확인합니다."""
    return {
        "status": "healthy",
        "environment": "service-server"
    }
