from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SeverityLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogBase(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    severity: SeverityLevel
    source: str = Field(..., min_length=1, max_length=255)

class LogCreate(LogBase):
    timestamp: Optional[datetime] = None

class LogUpdate(BaseModel):
    message: Optional[str] = Field(None, min_length=1, max_length=5000)
    severity: Optional[SeverityLevel] = None
    source: Optional[str] = Field(None, min_length=1, max_length=255)
    timestamp: Optional[datetime] = None

class LogResponse(LogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class LogListResponse(BaseModel):
    items: List[LogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class LogFiltering(BaseModel):
    severity: Optional[str] = None
    source: Optional[str] = None
    count: int
    date: Optional[str] = None

class LogFilteringResponse(BaseModel):
    aggregations: List[LogFiltering]
    total_count: int
