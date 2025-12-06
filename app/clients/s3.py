import boto3
import uuid as uuid_lib
from config.settings import settings


class CodeS3Client:
    """사용자 코드를 위한 S3 클라이언트입니다.

    코드 객체는 `AWS_CODE_REGION` / `AWS_CODE_BUCKET` 설정을 사용합니다.
    """

    def __init__(self) -> None:
        client_kwargs = {
            "region_name": settings.AWS_CODE_REGION,
        }
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs.update(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        if settings.AWS_SESSION_TOKEN:
            client_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

        self.s3_client = boto3.client("s3", **client_kwargs)
        self.bucket_name = settings.AWS_CODE_BUCKET

    def upload_code(self, project: str, code: str, language: str) -> str:
        """소스 코드를 코드 버킷에 업로드하고 객체 키를 반환합니다.

        Args:
            project: 프로젝트 이름.
            code: 업로드할 소스 코드 문자열.
            language: 프로그래밍 언어 이름.

        Returns:
            생성된 S3 객체 키.

        Raises:
            Exception: 업로드 실패 시 예외를 발생합니다.
        """
        try:
            filename = f"{uuid_lib.uuid4()}"
            postfix = {
                "python": ".py",
                "node": ".js",
                "java": ".java"
            }[language.lower()]

            s3_key = f"{project}/{language.lower()}/{filename}{postfix}"

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


class LogS3Client:
    """실행 로그를 위한 S3 클라이언트입니다.

    로그 객체는 `AWS_LOG_REGION` / `AWS_LOG_BUCKET` 설정을 사용합니다.
    """

    def __init__(self) -> None:
        client_kwargs = {
            "region_name": settings.AWS_LOG_REGION,
        }
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs.update(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        if settings.AWS_SESSION_TOKEN:
            client_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

        self.s3_client = boto3.client("s3", **client_kwargs)
        self.bucket_name = settings.AWS_LOG_BUCKET

    def get_log(self, key: str) -> str | None:
        """로그 버킷에서 지정한 키의 로그 파일을 조회합니다.

        Args:
            key: 조회할 로그 파일의 S3 객체 키.

        Returns:
            로그 파일 내용 문자열 또는 실패 시 None.
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read().decode("utf-8")
        except Exception:
            return None
