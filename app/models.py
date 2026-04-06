from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from datetime import datetime
from .database import Base

class LogEvent(Base):
    __tablename__ = "log_events"

    id = Column(Integer, primary_key=True, index=True)
    original_log = Column(String, nullable=False)
    cleaned_log = Column(String, nullable=False)
    cluster_id = Column(Integer, index=True)
    distance = Column(Float)
    is_anomaly = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
