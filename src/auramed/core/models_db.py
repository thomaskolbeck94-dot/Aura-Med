from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=True)
    checkout_session_id = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    api_keys = relationship("APIKey", back_populates="client")

class APIKey(Base):
    __tablename__ = "api_keys_saas"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    total_scans = Column(Integer, default=0)
    last_scan_at = Column(DateTime, nullable=True)
    
    client = relationship("Client", back_populates="api_keys")
