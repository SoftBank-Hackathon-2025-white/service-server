from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from config.db import Base


class LogORM(Base):
    """실행 로그 정보를 저장하는 ORM 엔티티입니다.

    S3에 저장된 로그 파일의 메타데이터를 관리합니다.
    """

    __tablename__ = "logs"

    log_key: str = Column(String(500), primary_key=True, nullable=False)
    job_id: str = Column(String(36), ForeignKey("jobs.job_id"), nullable=False, index=True)
    logs_url: str = Column(String(500), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    job = relationship("JobORM", back_populates="logs")

    __table_args__ = (
        Index("ix_logs_job_id", "job_id"),
        Index("ix_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<LogORM(log_key={self.log_key}, job_id={self.job_id})>"
