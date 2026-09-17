from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import config
from .models import Base

import os
DB_PATH = os.environ.get("VERIDOC_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "veridoc.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
