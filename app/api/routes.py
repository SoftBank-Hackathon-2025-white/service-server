from sqlalchemy.orm import Session
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    BackgroundTasks,
    Depends,
    Query,
)

from config.db import get_db
from app.models.code import CodeUploadRequest
from app.models.job import JobResponse, JobStatus, JobStatusResponse
from app.models.project import ProjectResponse
from app.models.execution import ExecutionRequest
from app.services.job import JobService
from app.services.project import ProjectService
from app.services.execution import ExecutionService
from app.services.s3 import S3Service
from app.services.cloudwatch import ResourceService, CloudWatchClient
from app.models.cloudwatch import (
    AvailableMetricsResponse,
    ClusterMetricsResponse,
    CloudWatchMetricPoint,
)

router = APIRouter()


def get_job_service(db: Session = Depends(get_db)) -> JobService:
    return JobService(db)


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


def get_execution_service(db: Session = Depends(get_db)) -> ExecutionService:
    return ExecutionService(db)


def get_s3_service(db: Session = Depends(get_db)) -> S3Service:
    return S3Service(db)


def get_cloudwatch_client() -> CloudWatchClient:
    return CloudWatchClient()


def get_resource_service(
    cw_client: CloudWatchClient = Depends(get_cloudwatch_client),
) -> ResourceService:
    return ResourceService(cw_client=cw_client)


async def run_execution_and_update_job(
    jobId: str,
    execution_request: ExecutionRequest,
    job_service: JobService,
    execution_service: ExecutionService,
) -> None:
    """Execution Engine 실행 후 Job 상태와 결과를 갱신하는 비동기 작업입니다."""
    try:
        result = await execution_service.submit_execution(execution_request)

        if result:
            job_service.update_job_status(jobId, JobStatus.SUCCESS)
            job_service.update_job_result(jobId, result.dict())
        else:
            job_service.update_job_status(jobId, JobStatus.FAILED)
    except Exception:
        job_service.update_job_status(jobId, JobStatus.FAILED)


@router.post("/upload", response_model=JobResponse)
async def upload_code(
    code_request: CodeUploadRequest,
    s3_service: S3Service = Depends(get_s3_service),
    job_service: JobService = Depends(get_job_service),
) -> JobResponse:
    """사용자 코드를 업로드하고 새로운 Job을 생성합니다."""
    if code_request.language not in ("python", "node"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: {code_request.language}",
        )

    try:
        code_key = await s3_service.upload_user_code(
            project=code_request.project,
            code=code_request.code,
            language=code_request.language,
        )
        if not code_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload code to storage",
            )

        job = job_service.create_job(code_request, code_key)
        response = job_service.to_response(job, "Code uploaded successfully")
        return JobResponse(**response.dict())

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload code",
        )


@router.post("/execute/{jobId}", response_model=JobResponse)
async def execute_code(
    jobId: str,
    background_tasks: BackgroundTasks,
    input_data: str = "",
    job_service: JobService = Depends(get_job_service),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> JobResponse:
    """기존 Job에 대해 코드 실행을 비동기로 트리거합니다."""
    try:
        job = job_service.get_job(jobId)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {jobId} not found",
            )

        job_service.update_job_status(jobId, JobStatus.RUNNING)

        execution_request = ExecutionRequest(
            job_id=jobId,
            code_key=job.code_key,
            language=job.language,
            input=input_data,
            timeout=job.timeout_ms,
        )

        background_tasks.add_task(
            run_execution_and_update_job,
            jobId,
            execution_request,
            job_service,
            execution_service,
        )

        job = job_service.get_job(jobId) or job
        return job_service.to_response(job, "Execution started")

    except HTTPException:
        raise
    except Exception:
        job_service.update_job_status(jobId, JobStatus.FAILED)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger execution",
        )


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> list[ProjectResponse]:
    """저장된 모든 프로젝트를 조회합니다."""
    try:
        projects_orm = project_service.get_all_projects()
        return [project_service._orm_to_dto(p) for p in projects_orm]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects",
        )


@router.post("/project", response_model=ProjectResponse)
async def create_project(
    project_name: str,
    description: str = "",
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """새로운 프로젝트를 생성합니다."""
    try:
        project_orm = project_service.get_or_create_project(project_name, description)
        if not project_orm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create or retrieve project",
            )
        return project_service._orm_to_dto(project_orm)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )


@router.get("/projects/{project}/jobs", response_model=list[JobResponse])
async def list_jobs_by_project(
    project: str,
    limit: int = 100,
    job_service: JobService = Depends(get_job_service),
) -> list[JobResponse]:
    """특정 프로젝트에 속한 Job 목록을 조회합니다."""
    try:
        jobs = job_service.list_jobs_by_project(project, limit=limit)
        return [job_service.to_response(j) for j in jobs]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs for project",
        )


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    limit: int = 100,
    job_service: JobService = Depends(get_job_service),
) -> list[JobResponse]:
    """전체 Job 목록을 조회합니다."""
    try:
        jobs = job_service.list_jobs(limit=limit)
        return [job_service.to_response(j) for j in jobs]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs",
        )


@router.get("/log", response_model=str)
async def get_log_file(
    log_key: str,
    s3_service: S3Service = Depends(get_s3_service),
) -> str:
    """S3에 저장된 로그 파일을 조회합니다."""
    content = s3_service.get_log_file(log_key)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log file {log_key} not found",
        )
    return content


@router.get("/cloudwatch/{clusterName}/metrics", response_model=AvailableMetricsResponse)
def get_available_ecs_metrics(
    clusterName: str,
    resource_service: ResourceService = Depends(get_resource_service),
) -> AvailableMetricsResponse:
    """ECS 클러스터의 사용 가능한 CloudWatch 메트릭 목록을 조회합니다."""
    metric_names = resource_service.list_cluster_metric_names(clusterName)

    if not metric_names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No metrics found for cluster in CloudWatch",
        )

    return AvailableMetricsResponse(
        cluster_name=clusterName,
        metric_names=metric_names,
    )


@router.get("/cloudwatch/{clusterName}", response_model=ClusterMetricsResponse)
def read_ecs_cluster_metrics(
    clusterName: str,
    minutes: int = Query(10, ge=1, le=60),
    period: int = Query(60, ge=10),
    resource_service: ResourceService = Depends(get_resource_service),
) -> ClusterMetricsResponse:
    """ECS 클러스터의 최근 CPU 및 메모리 사용률 메트릭을 조회합니다."""
    try:
        points = resource_service.get_recent_cpu_memory_utilization(
            cluster_name=clusterName,
            minutes=minutes,
            period=period,
        )

        if not points:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No metric datapoints found for cluster",
            )

        return ClusterMetricsResponse(
            cluster_name=clusterName,
            metrics=points,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ECS cluster metrics",
        )


@router.get("/health")
async def health_check() -> dict:
    """서비스 헬스 체크 정보를 반환합니다."""
    return {
        "status": "healthy",
        "environment": "service-server",
    }


@router.get("/jobs/{jobId}/status", response_model=JobStatusResponse)
async def get_job_status(
    jobId: str,
    job_service: JobService = Depends(get_job_service),
) -> JobStatusResponse:
    """Job의 현재 상태를 조회합니다.
    
    Args:
        jobId: 조회할 Job의 ID.
        
    Returns:
        Job의 상태 정보 (상태, 생성 시각, 실행 시작/완료 시각 등).
        
    Raises:
        HTTPException: Job을 찾을 수 없으면 404 반환.
    """
    try:
        job = job_service.get_job(jobId)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {jobId} not found",
            )
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            project=job.project,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            timeout_ms=job.timeout_ms,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status",
        )
