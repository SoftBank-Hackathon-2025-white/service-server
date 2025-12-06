from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config.settings import settings


engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """데이터베이스 세션을 생성하고 반환합니다.

    FastAPI 의존성 주입용 제너레이터입니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
