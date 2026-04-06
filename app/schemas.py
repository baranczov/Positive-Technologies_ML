from pydantic import BaseModel
from datetime import datetime

class LogRequest(BaseModel):
    log_message: str

class LogResponse(BaseModel):
    id: int
    original_log: str
    cleaned_log: str
    cluster_id: int
    distance: float
    is_anomaly: bool
    created_at: datetime

    class Config:
        from_attributes = True 