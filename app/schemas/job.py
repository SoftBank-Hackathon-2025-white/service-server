from sqlalchemy import Column, String, DateTime, Integer, Text, Enum, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from config.db import Base
from app.models.job import JobStatus


class JobORM(Base):
    """코드 실행 Job을 저장하는 ORM 엔티티입니다.

    프로젝트 내의 각 코드 실행을 추적하고 상태를 관리합니다.
    """

    __tablename__ = "jobs"

    job_id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    project: str = Column(String(255), ForeignKey("projects.project"), nullable=False, index=True)
    code_key: str = Column(String(500), nullable=False)
    language: str = Column(String(50), nullable=False)
    status: JobStatus = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at: datetime = Column(DateTime(timezone=True), nullable=True)
    completed_at: datetime = Column(DateTime(timezone=True), nullable=True)
    timeout_ms: int = Column(Integer, default=5000, nullable=False)
    result: dict = Column(JSON, nullable=True)

    # 관계 정의
    executions = relationship("ExecutionORM", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("LogORM", back_populates="job", cascade="all, delete-orphan")

    # 복합 인덱스
    __table_args__ = (
        Index("ix_jobs_project_status", "project", "status"),
        Index("ix_jobs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<JobORM(job_id={self.job_id}, project={self.project}, status={self.status})>"
