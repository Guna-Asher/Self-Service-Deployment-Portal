from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.deployment import DeploymentCreate, DeploymentResponse
from app.services import deployment_service

router = APIRouter(prefix="/applications/{app_id}/deployments", tags=["deployments"])

@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
def deploy_version(
    app_id: UUID,
    payload: DeploymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):



    return deployment_service.trigger_deployment(db, app_id, payload, current_user, background_tasks)

@router.get("/", response_model=list[DeploymentResponse])
def list_deployments(
    app_id: UUID,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deployment_service.list_deployments(db, app_id, current_user, skip, limit)

@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(
    app_id: UUID,
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deployment_service.get_deployment(db, app_id, deployment_id, current_user)

@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
def rollback_deployment(
    app_id: UUID,
    deployment_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return deployment_service.rollback_deployment(db, app_id, deployment_id, current_user, background_tasks)