from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

def get_db():
    """
    데이터베이스 세션을 생성하고 반환하는 의존성 함수입니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
