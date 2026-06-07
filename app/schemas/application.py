from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

class ApplicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    repository_url: HttpUrl | None = None

class ApplicationResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    repository_url: str | None
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True