from app.clients.s3_client import S3Client
from typing import Optional


class S3Service:
    """S3에 코드 객체를 저장하는 서비스 계층입니다."""

    def __init__(self) -> None:
        self.s3_client = S3Client()
    
    async def upload_user_code(self, code: str, language: str) -> Optional[str]:
        """사용자 코드를 S3에 업로드합니다.

        Args:
            code: 업로드할 코드 문자열.
            language: 프로그래밍 언어 이름.

        Returns:
            생성된 S3 객체 키 또는 실패 시 None.
        """
        try:
            return self.s3_client.upload_code(code, language)
        except Exception:
            return None
