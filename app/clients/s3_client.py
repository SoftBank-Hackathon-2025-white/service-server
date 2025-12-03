import boto3
from typing import Optional
from config.settings import settings


class S3Client:
    """AWS S3에 코드 객체를 업로드·다운로드·삭제하는 클라이언트입니다."""

    def __init__(self) -> None:
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET

    async def upload_code(self, code: str, language: str, filename: Optional[str] = None) -> str:
        """소스 코드를 S3에 업로드하고 객체 키를 반환합니다.

        Args:
            code: 업로드할 소스 코드 문자열.
            language: 프로그래밍 언어 이름.
            filename: 선택적 파일 이름(확장자는 자동 보정).

        Returns:
            생성된 S3 객체 키.

        Raises:
            Exception: 업로드 실패 시 예외를 발생합니다.
        """
        try:
            import uuid as uuid_lib

            extension_map = {
                "python": "py",
                "node": "js",
                "java": "java"
            }

            extension = extension_map.get(language.lower(), "txt")

            if not filename:
                filename = f"{uuid_lib.uuid4()}.{extension}"
            elif not filename.endswith(f".{extension}"):
                filename = f"{filename}.{extension}"

            s3_key = f"{language.lower()}/{filename}"

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=code.encode("utf-8"),
                ContentType="text/plain",
                Metadata={"language": language},
            )

            return s3_key

        except Exception as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    async def download_code(self, s3_key: str) -> Optional[str]:
        """S3 객체 키로 코드를 다운로드합니다.

        Args:
            s3_key: 다운로드할 S3 객체 키.

        Returns:
            코드 문자열 또는 실패 시 None.
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            code = response["Body"].read().decode("utf-8")
            return code
        except Exception:
            return None

    async def delete_code(self, s3_key: str) -> bool:
        """S3에 저장된 코드 객체를 삭제합니다.

        Args:
            s3_key: 삭제할 S3 객체 키.

        Returns:
            성공 시 True, 실패 시 False.
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return True
        except Exception:
            return False
