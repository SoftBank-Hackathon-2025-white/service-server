from typing import Optional, Dict, List, Any
from app.models.job import Job, JobStatus, JobResponse
from app.models.code import CodeUploadRequest
from app.schemas.job import JobORM
from app.services.project import ProjectService
from datetime import datetime
from sqlalchemy.orm import Session
import uuid


class JobService:
    """Job의 라이프사이클을 관리하는 서비스입니다.

    RDS 데이터베이스를 사용하여 Job을 생성, 조회, 상태 업데이트합니다.
    """
    
    def __init__(self, db: Session) -> None:
        """데이터베이스 세션을 초기화합니다."""
        self.db = db
        self.project_service = ProjectService(db)
    
    def create_job(self, code_request: CodeUploadRequest, code_key: str) -> Job:
        """코드 업로드 요청으로 Job을 생성합니다.

        Args:
            code_request: 업로드된 코드 정보.
            code_key: S3에 저장된 코드 키.

        Returns:
            생성된 Job 객체.
        """
        project_orm = self.project_service.get_or_create_project(
            code_request.project,
            code_request.description
        )

        job_orm = JobORM(
            job_id=str(uuid.uuid4()),
            project_id=project_orm.project_id,
            code_key=code_key,
            language=code_request.language,
            status=JobStatus.PENDING,
            timeout_ms=30000  
        )
        self.db.add(job_orm)
        self.db.commit()
        
        return self._orm_to_dto(job_orm)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Job ID로 Job을 조회합니다."""
        job_orm = self.db.query(JobORM).filter(JobORM.job_id == job_id).first()
        return self._orm_to_dto(job_orm) if job_orm else None
    
    
    def list_jobs_by_project(self, project: str, limit: int = 100) -> List[Job]:
        """특정 프로젝트에 속한 Job 목록을 조회합니다.

        Args:
            project: 프로젝트 이름.
            limit: 최대 반환 개수.

        Returns:
            Job 객체 리스트.
        """
        project_orm = self.project_service.get_project(project)
        if not project_orm:
            return []
        
        job_orms = self.db.query(JobORM).filter(
            JobORM.project_id == project_orm.project_id
        ).order_by(JobORM.created_at.desc()).limit(limit).all()
        
        return [self._orm_to_dto(job_orm) for job_orm in job_orms]
    
    def update_job_status(self, job_id: str, status: JobStatus) -> bool:
        """Job 상태를 업데이트합니다.

        Args:
            job_id: 대상 Job ID.
            status: 변경할 상태.

        Returns:
            업데이트 성공 여부.
        """
        job_orm = self.db.query(JobORM).filter(JobORM.job_id == job_id).first()
        if not job_orm:
            return False
        
        job_orm.status = status
        job_orm.updated_at = datetime.utcnow()
        
        if status == JobStatus.RUNNING:
            job_orm.started_at = datetime.utcnow()
        elif status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.TIMEOUT, JobStatus.CANCELLED]:
            job_orm.completed_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def update_job_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """실행 결과를 Job에 저장합니다.

        Args:
            job_id: 대상 Job ID.
            result: 엔진에서 반환된 실행 결과 딕셔너리.

        Returns:
            업데이트 성공 여부.
        """
        job_orm = self.db.query(JobORM).filter(JobORM.job_id == job_id).first()
        if not job_orm:
            return False

        job_orm.result = result
        job_orm.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def list_jobs(self, limit: int = 100) -> List[Job]:
        """Job 목록을 생성 시각 기준 내림차순으로 반환합니다.

        Args:
            limit: 최대 반환 개수.

        Returns:
            Job 객체 리스트.
        """
        job_orms = self.db.query(JobORM).order_by(JobORM.created_at.desc()).limit(limit).all()
        return [self._orm_to_dto(job_orm) for job_orm in job_orms]
    
    def to_response(self, job: Job, message: str = "") -> JobResponse:
        """Job DTO를 JobResponse로 변환합니다.
        
        최신 execution 정보(log_key, logs_url)도 포함합니다.
        """
        # 최신 execution 조회
        job_orm = self.db.query(JobORM).filter(JobORM.job_id == job.job_id).first()
        log_key = None
        logs_url = None
        
        if job_orm and job_orm.executions:
            latest_execution = max(job_orm.executions, key=lambda e: e.completed_at)
            log_key = latest_execution.log_key
            logs_url = latest_execution.logs_url
        
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
            log_key=log_key,
            logs_url=logs_url,
            message=message or f"Job status: {job.status.value}",
            data=data,
        )
    
    def _orm_to_dto(self, job_orm: JobORM) -> Job:
        """JobORM을 Job DTO로 변환합니다."""
        return Job(
            job_id=job_orm.job_id,
            project=job_orm.project_rel.project,
            code_key=job_orm.code_key,
            language=job_orm.language,
            status=job_orm.status,
            created_at=job_orm.created_at,
            updated_at=job_orm.updated_at,
            started_at=job_orm.started_at,
            completed_at=job_orm.completed_at,
            timeout_ms=job_orm.timeout_ms,
            result=job_orm.result
        )
