from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.version import VersionCreate, VersionResponse
from app.services import version_service

router = APIRouter()

@router.post("/applications/{app_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED, tags=["versions"])
def create_version(app_id: UUID, payload: VersionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return version_service.create_version(db, app_id, payload, current_user)

@router.get("/applications/{app_id}/versions", response_model=list[VersionResponse], tags=["versions"])
def list_versions(app_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return version_service.list_versions(db, app_id, current_user)

@router.get("/applications/{app_id}/versions/{version_id}", response_model=VersionResponse, tags=["versions"])
def get_version(app_id: UUID, version_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return version_service.get_version(db, app_id, version_id, current_user)