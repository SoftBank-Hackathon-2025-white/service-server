from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """환경 변수를 기반으로 서버 설정을 불러옵니다."""

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    EXECUTION_ENGINE_URL: str = "http://localhost:9000"
    EXECUTION_ENGINE_TIMEOUT: int = 30000
    EXECUTION_ENGINE_BASE_URL: str = "http://softbank-exec-engine-alb-423729816.ap-northeast-2.elb.amazonaws.com"
    EXECUTION_ENGINE_PYTHON_RUN_URL: str = "http://softbank-exec-engine-alb-423729816.ap-northeast-2.elb.amazonaws.com/python/run"
    EXECUTION_ENGINE_NODE_RUN_URL: str = "http://softbank-exec-engine-alb-423729816.ap-northeast-2.elb.amazonaws.com/node/run"

    AWS_REGION: str = "ap-northeast-1"
    AWS_S3_BUCKET: str = "softbank-code-bucket"
    AWS_DYNAMODB_TABLE: str = "execution-metrics"

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/server.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
