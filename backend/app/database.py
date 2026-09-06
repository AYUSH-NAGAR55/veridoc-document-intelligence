"""SQLAlchemy engine/session setup. Works with SQLite, PostgreSQL, or MySQL
purely by changing DATABASE_URL - no code changes needed."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path and db_path != ":memory:":
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401 ensures models are registered
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.index_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)
