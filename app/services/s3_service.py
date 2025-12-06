from app.clients.s3_client import S3Client
from typing import Optional


class S3Service:
    """S3에 코드 객체를 저장하는 서비스 계층입니다.

    내부적으로 `S3Client`를 사용해 코드 문자열을 S3 객체로 업로드합니다.
    """

    def __init__(self) -> None:
        self.s3_client = S3Client()
    
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
            return self.s3_client.upload_code(project, code, language)
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
            response = self.s3_client.s3_client.get_object(
                Bucket=self.s3_client.bucket_name,
                Key=log_key
            )
            print(response)
            # content = response['Body'].read().decode('utf-8')
            return response
        except Exception:
            return None
        