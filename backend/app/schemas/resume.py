"""Resume schemas."""
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ResumeResponse(BaseModel):
    """Resume response."""
    id: UUID
    file_type: Optional[str] = None
    raw_narrative: Optional[str] = None
    parsed_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    """List of resumes."""
    resumes: list[ResumeResponse]
    total: int
