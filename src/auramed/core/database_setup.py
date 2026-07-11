import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auramed.core.models_db import Base

DB_PATH = os.environ.get("AURAMED_DB_PATH", "auramed.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_saas_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
