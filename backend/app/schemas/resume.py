"""Resume schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ResumeResponse(BaseModel):
    """Resume response."""
    id: str
    title: str
    raw_narrative: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    """List of resumes."""
    resumes: list[ResumeResponse]
    total: int
