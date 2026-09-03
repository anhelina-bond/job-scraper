from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any

# Schema for creating a new log entry
class AgentLogCreate(BaseModel):
    step_name: str
    tool_called: Optional[str] = None
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None

# Schema for Application data
class ApplicationBase(BaseModel):
    job_url: Optional[str] = None
    job_title: str
    company: str
    match_score: float
    cover_letter: str

class ApplicationCreate(ApplicationBase):
    raw_job_text: str

class ApplicationResponse(ApplicationBase):
    id: int
    date_applied: datetime

    class Config:
        from_attributes = True