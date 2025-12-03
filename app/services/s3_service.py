from app.clients.s3_client import S3Client
from typing import Optional


class S3Service:
    """S3에 코드 객체를 저장·조회·삭제하는 서비스 계층입니다."""

    def __init__(self) -> None:
        self.s3_client = S3Client()
    
    async def upload_user_code(self, code: str, language: str, filename: str = None) -> Optional[str]:
        """사용자 코드를 S3에 업로드합니다.

        Args:
            code: 업로드할 코드 문자열.
            language: 프로그래밍 언어 이름.
            filename: 선택적 파일 이름(없으면 UUID 자동 생성).

        Returns:
            생성된 S3 객체 키 또는 실패 시 None.
        """
        try:
            return await self.s3_client.upload_code(code, language, filename)
        except Exception:
            return None
    
    async def retrieve_code(self, s3_key: str) -> Optional[str]:
        """S3에서 코드 객체를 조회합니다.

        Args:
            s3_key: 조회할 S3 객체 키.

        Returns:
            코드 문자열 또는 실패 시 None.
        """
        return await self.s3_client.download_code(s3_key)
    
    async def remove_code(self, s3_key: str) -> bool:
        """S3에서 코드 객체를 삭제합니다.

        Args:
            s3_key: 삭제할 S3 객체 키.

        Returns:
            성공 시 True, 실패 시 False.
        """
        return await self.s3_client.delete_code(s3_key)
