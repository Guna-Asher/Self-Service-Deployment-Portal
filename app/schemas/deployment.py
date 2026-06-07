from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

class DeploymentCreate(BaseModel):
    version_id: UUID

class DeploymentResponse(BaseModel):
    id: UUID
    application_id: UUID
    version_id: UUID
    deployed_by: UUID
    status: str
    started_at: datetime
    finished_at: datetime | None
    previous_deployment_id: UUID | None
    rollback_of_deployment_id: UUID | None

    class Config:
        orm_mode = True