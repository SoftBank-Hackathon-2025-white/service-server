import boto3
import uuid as uuid_lib
from config.settings import settings


class S3Client:
    """AWS S3에 코드 객체를 업로드하는 저수준 클라이언트입니다.

    boto3 클라이언트를 래핑하여 버킷 이름, 자격 증명 설정을 숨깁니다.
    """

    def __init__(self) -> None:
        client_kwargs = {
            "region_name": settings.AWS_REGION,
        }
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs.update(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        if settings.AWS_SESSION_TOKEN:
            client_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

        self.s3_client = boto3.client("s3", **client_kwargs)
        self.bucket_name = settings.AWS_S3_BUCKET

    def upload_code(self, code: str, language: str) -> str:
        """소스 코드를 S3에 업로드하고 객체 키(code_key)를 반환합니다.

        Args:
            code: 업로드할 소스 코드 문자열.
            language: 프로그래밍 언어 이름.

        Returns:
            생성된 S3 객체 키.

        Raises:
            Exception: 업로드 실패 시 예외를 발생합니다.
        """
        try:
            filename = f"{uuid_lib.uuid4()}"

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
