import uuid
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

def generate_uuid() -> str:
    return str(uuid.uuid4())

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

class MonitoredFolder(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    path: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=now_utc)

class FileEvent(BaseModel):
    event_id: str = Field(default_factory=generate_uuid)
    folder_id: str
    filename: str
    filepath: str
    size_bytes: int
    extension: Optional[str] = None
    file_hash: Optional[str] = None
    file_mtime: float
    detected_at: datetime = Field(default_factory=now_utc)

class ErrorEvent(BaseModel):
    error_id: str = Field(default_factory=generate_uuid)
    folder_id: str
    event_id: Optional[str] = None
    error_type: str
    message: str
    occurred_at: datetime = Field(default_factory=now_utc)
