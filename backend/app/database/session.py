from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from app.config.settings import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_engine() -> Engine:
    """Return the SQLAlchemy engine instance."""
    return engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

