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
    _migrate_add_owner_columns()


def _migrate_add_owner_columns():
    """Adds owner_id to pre-existing tables created before multi-user isolation
    was introduced. SQLite/Postgres/MySQL all support this exact ALTER TABLE
    syntax. Existing rows get owner_id=NULL, which means they belong to no one
    and become inaccessible to everyone post-upgrade - a fail-closed default
    rather than accidentally exposing old data to whichever user asks first."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    try:
        existing_tables = set(inspector.get_table_names())
    except Exception:
        return

    targets = [("documents", "owner_id"), ("query_logs", "owner_id")]
    for table, column in targets:
        if table not in existing_tables:
            continue
        cols = {c["name"] for c in inspector.get_columns(table)}
        if column in cols:
            continue
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR(64)"))
