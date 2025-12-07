from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config.settings import settings


Base = declarative_base()

engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """데이터베이스 테이블을 자동으로 생성합니다.
    
    모든 ORM 엔티티(schemas)를 Base에 등록한 후 호출해야 합니다.
    이미 존재하는 테이블이나 인덱스는 건너뜁니다.
    """
    Base.metadata.create_all(bind=engine, checkfirst=True)


def get_db():
    """데이터베이스 세션을 생성하고 반환합니다.

    FastAPI 의존성 주입용 제너레이터입니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
