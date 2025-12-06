from pydantic_settings import BaseSettings
from pydantic import computed_field


class Settings(BaseSettings):
    """환경 변수를 기반으로 서버 실행 설정을 관리합니다.

    환경마다 다른 포트, 로그 레벨, AWS 자격 증명 및
    Execution Engine URL을 중앙에서 관리합니다.
    """

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    EXECUTION_ENGINE_URL: str = "http://localhost:9000"
    EXECUTION_ENGINE_TIMEOUT: int = 30000
    EXECUTION_ENGINE_BASE_URL: str = "http://softbank-exec-engine-alb-423729816.ap-northeast-2.elb.amazonaws.com"
    EXECUTION_ENGINE_PYTHON_RUN_URL: str = f"{EXECUTION_ENGINE_BASE_URL}/python/run"
    EXECUTION_ENGINE_NODE_RUN_URL: str = f"{EXECUTION_ENGINE_BASE_URL}/node/run"

    RESOURCE_URL: str = "http://softbank-exec-engine-alb-423729816.ap-northeast-2.elb.amazonaws.com/monitor/"
    RESOURCE_PYTHON_URL: str = f"{RESOURCE_URL}/python"
    RESOURCE_NODE_URL: str = f"{RESOURCE_URL}/node"

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_SESSION_TOKEN: str | None = None

    AWS_CODE_REGION: str = "ap-northeast-2"
    AWS_CODE_BUCKET: str = "softbank-code-bucket"

    AWS_LOG_REGION: str = "ap-northeast-2"
    AWS_LOG_BUCKET: str = "softbank-log-bucket"

    AWS_RDS_HOST: str | None = None
    AWS_RDS_PORT: int | None = None
    AWS_RDS_DBNAME: str | None = None
    AWS_RDS_USERNAME: str | None = None
    AWS_RDS_PASSWORD: str | None = None 

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """RDS 연결 문자열을 동적으로 생성합니다."""
        return f"mysql+pymysql://{self.AWS_RDS_USERNAME}:{self.AWS_RDS_PASSWORD}@{self.AWS_RDS_HOST}:{self.AWS_RDS_PORT}/{self.AWS_RDS_DBNAME}"
        
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
