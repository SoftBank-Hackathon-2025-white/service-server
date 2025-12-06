from typing import Optional, Dict, List, Any
from app.models.job import Job, JobStatus, JobResponse
from app.models.code import CodeUploadRequest
from datetime import datetime


class JobService:
    """Job의 라이프사이클을 관리하는 서비스입니다.

    생성, 조회, 상태 업데이트, 목록 조회를 처리하며 현재는 인메모리 저장소를 사용합니다.
    """
    
    def __init__(self) -> None:
        self.jobs: Dict[str, Job] = {}
    
    def create_job(self, code_request: CodeUploadRequest, code_key: str) -> Job:
        """코드 업로드 요청으로 Job을 생성합니다.

        Args:
            code_request: 업로드된 코드 정보.
            code_key: s3에 저장된 코드 키.

        Returns:
            생성된 Job 객체.
        """
        job = Job(
            project=code_request.project,
            code_key=code_key,
            language=code_request.language,
            status=JobStatus.PENDING
        )
        self.jobs[job.job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Job ID로 Job을 조회합니다."""
        return self.jobs.get(job_id)
    
    def list_jobs_by_project(self, project: str, limit: int = 100) -> List[Job]:
        """특정 프로젝트에 속한 Job 목록을 조회합니다.

        Args:
            project: 프로젝트 이름.
            limit: 최대 반환 개수.

        Returns:
            Job 객체 리스트.
        """
        filtered_jobs = [
            job for job in self.jobs.values()
            if job.code_key.startswith(f"{project}/")
        ]
        filtered_jobs.sort(key=lambda j: j.created_at, reverse=True)
        return filtered_jobs[:limit]
    
    def update_job_status(self, job_id: str, status: JobStatus) -> bool:
        """Job 상태를 업데이트합니다.

        Args:
            job_id: 대상 Job ID.
            status: 변경할 상태.

        Returns:
            업데이트 성공 여부.
        """
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        job.status = status
        job.updated_at = datetime.utcnow()
        
        if status == JobStatus.RUNNING:
            job.started_at = datetime.utcnow()
        elif status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.TIMEOUT, JobStatus.CANCELLED]:
            job.completed_at = datetime.utcnow()
        
        return True
    
    def update_job_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """실행 결과를 Job에 저장합니다.

        Args:
            job_id: 대상 Job ID.
            result: 엔진에서 반환된 실행 결과 딕셔너리.

        Returns:
            업데이트 성공 여부.
        """
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]
        job.result = result
        job.updated_at = datetime.utcnow()
        return True
    
    def list_jobs(self, limit: int = 100) -> List[Job]:
        """Job 목록을 생성 시각 기준 내림차순으로 반환합니다.

        Args:
            limit: 최대 반환 개수.

        Returns:
            Job 객체 리스트.
        """
        jobs_list = list(self.jobs.values())
        jobs_list.sort(key=lambda j: j.created_at, reverse=True)
        return jobs_list[:limit]
    
    def to_response(self, job: Job, message: str = "") -> JobResponse:
        data: Dict[str, Any] = {
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "code_key": job.code_key,
            "language": job.language,
        }

        if job.result:
            data["result"] = job.result

        return JobResponse(
            job_id=job.job_id,
            project=job.project,
            code_key=job.code_key,
            status=job.status,
            message=message or f"Job status: {job.status.value}",
            data=data,
        )
