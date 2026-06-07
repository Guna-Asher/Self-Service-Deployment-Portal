from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

class VersionCreate(BaseModel):
    version_tag: str = Field(..., min_length=1, max_length=100)
    image_name: str = Field(..., min_length=1, max_length=255)

class VersionResponse(BaseModel):
    id: UUID
    application_id: UUID
    version_tag: str
    image_name: str
    created_at: datetime

    class Config:
        orm_mode = True