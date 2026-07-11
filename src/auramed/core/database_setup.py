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
    
    # Auto-migration for daily_scans (added in v0.2)
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("ALTER TABLE api_keys_saas ADD COLUMN daily_scans INTEGER DEFAULT 0;")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    # Auto-migration for telegram fields (added in v0.3)
    try:
        conn.execute("ALTER TABLE clients ADD COLUMN telegram_chat_id TEXT UNIQUE;")
        conn.execute("ALTER TABLE clients ADD COLUMN ha_webhook_url TEXT;")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    finally:
        if 'conn' in locals():
            conn.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
