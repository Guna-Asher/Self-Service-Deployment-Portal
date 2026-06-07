from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return application_service.create_application(db, payload, current_user)

@router.get("/", response_model=list[ApplicationResponse])
def list_applications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return application_service.list_applications(db, current_user)

@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(app_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return application_service.get_application(db, app_id, current_user)

@router.delete("/{app_id}")
def delete_application(app_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return application_service.delete_application(db, app_id, current_user)