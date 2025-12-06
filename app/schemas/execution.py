from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from config.db import Base


class ExecutionORM(Base):
    """코드 실행 결과를 저장하는 ORM 엔티티입니다.

    각 Job마다 하나 이상의 Execution 기록을 가질 수 있습니다.
    """

    __tablename__ = "executions"

    execution_id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    job_id: str = Column(String(36), ForeignKey("jobs.job_id"), nullable=False, index=True)
    stdout: str = Column(Text, default="", nullable=False)
    stderr: str = Column(Text, default="", nullable=False)
    logs_url: str = Column(String(500), nullable=True)
    error_message: str = Column(Text, nullable=True)
    completed_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    cpu_ms: float = Column(Float, nullable=True)
    memory_peak: float = Column(Float, nullable=True)
    duration_ms: float = Column(Float, nullable=True)

    job = relationship("JobORM", back_populates="executions")

    __table_args__ = (
        Index("ix_executions_job_id", "job_id"),
        Index("ix_executions_completed_at", "completed_at"),
    )

    def __repr__(self) -> str:
        return f"<ExecutionORM(execution_id={self.execution_id}, job_id={self.job_id})>"
