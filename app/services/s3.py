from app.clients.s3 import CodeS3Client, LogS3Client
from app.schemas.log import LogORM
from typing import Optional
from sqlalchemy.orm import Session
import uuid


class S3Service:
    """S3에 코드와 로그를 저장하고 메타데이터를 RDS에 기록하는 서비스입니다."""

    def __init__(self, db: Session) -> None:
        """S3 클라이언트와 데이터베이스 세션을 초기화합니다."""
        self.code_client = CodeS3Client()
        self.log_client = LogS3Client()
        self.db = db
    
    async def upload_user_code(self, project: str, code: str, language: str) -> Optional[str]:
        """사용자 코드를 S3에 업로드합니다.

        Args:
            project: 프로젝트 이름.
            code: 업로드할 코드 문자열.
            language: 프로그래밍 언어 이름.

        Returns:
            생성된 S3 객체 키 또는 실패 시 None.
        """
        try:
            return self.code_client.upload_code(project, code, language)
        except Exception:
            return None

    def get_log_file(self, log_key: str) -> Optional[str]:
        """S3에서 로그 파일을 조회합니다.
        
        Args:
            log_key: 조회할 로그 파일의 S3 객체 키.
            
        Returns:
            로그 파일 내용 문자열 또는 실패 시 None.
        """
        try:
            return self.log_client.get_log(log_key)
        except Exception:
            return None
    
    def save_log_metadata(self, job_id: str, logs_url: str) -> bool:
        """로그 메타데이터를 RDS에 저장합니다.
        
        Args:
            job_id: 대상 Job ID.
            logs_url: S3 로그 URL.
            
        Returns:
            저장 성공 여부.
        """
        try:
            log_orm = LogORM(
                log_key=str(uuid.uuid4()),
                job_id=job_id,
                logs_url=logs_url
            )
            self.db.add(log_orm)
            self.db.commit()
            return True
        except Exception:
            return False
        