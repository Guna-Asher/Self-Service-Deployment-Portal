from datetime import datetime, timezone
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.application import Application
from app.models.deployment import Deployment
from app.models.user import User
from app.models.version import Version
from app.schemas.deployment import DeploymentCreate
from app.services.docker_service import DockerDeployer, DockerDeployError
from app.services.log_service import add_log

def _build_container_name(app_name: str, version_tag: str) -> str:
    safe_name = app_name.replace(" ", "-").lower()
    safe_version = version_tag.replace(" ", "-").lower()
    return f"app-{safe_name}-{safe_version}"

def _execute_deployment(
    deployment_id: UUID,
    app_name: str,
    version_tag: str,
    image_name: str,
    source_deployment_id: UUID | None = None,
):
    db = SessionLocal()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            return

        deployment.status = "in_progress"
        db.commit()

        container_name = _build_container_name(app_name, version_tag)
        deployer = DockerDeployer()

        # Log callback that stores in DB using the same session
        def log_callback(msg: str, level: str = "info"):
            add_log(db, deployment_id, msg, level)
            db.commit()   # commit each log immediately

        # Parse port binding from settings
        from app.core.config import settings
        host_port_str, container_port_str = settings.DEFAULT_PORT_BINDING.split(":")
        port_bindings = {f"{container_port_str}/tcp": int(host_port_str)}

        deployer.deploy(
            image_name=image_name,
            container_name=container_name,
            port_bindings=port_bindings,
            log_callback=log_callback,
        )

        deployment.status = "success"
        deployment.finished_at = datetime.now(timezone.utc)

        if source_deployment_id:
            source = db.query(Deployment).filter(Deployment.id == source_deployment_id).first()
            if source:
                source.status = "rolled_back"
                source.finished_at = datetime.now(timezone.utc)

        db.commit()
    except DockerDeployError as e:
        deployment.status = "failed"
        deployment.finished_at = datetime.now(timezone.utc)
        add_log(db, deployment_id, f"Deployment failed: {str(e)}", "error")
        db.commit()
    except Exception as e:
        deployment.status = "failed"
        deployment.finished_at = datetime.now(timezone.utc)
        add_log(db, deployment_id, f"Unexpected error: {str(e)}", "error")
        db.commit()
    finally:
        db.close()

def trigger_deployment(
    db: Session,
    app_id: UUID,
    payload: DeploymentCreate,
    user: User,
    background_tasks: BackgroundTasks,
) -> Deployment:
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your application")

    version = db.query(Version).filter(Version.id == payload.version_id, Version.application_id == app_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found for this application")

    previous = (
        db.query(Deployment)
        .filter(
            Deployment.application_id == app_id,
            Deployment.status.in_(["success", "in_progress"]),
        )
        .order_by(Deployment.started_at.desc())
        .first()
    )

    deployment = Deployment(
        application_id=app_id,
        version_id=version.id,
        deployed_by=user.id,
        status="pending",
        previous_deployment_id=previous.id if previous else None,
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    background_tasks.add_task(
        _execute_deployment,
        deployment_id=deployment.id,
        app_name=app.name,
        version_tag=version.version_tag,
        image_name=version.image_name,
    )
    return deployment

def rollback_deployment(
    db: Session,
    app_id: UUID,
    source_deployment_id: UUID,
    user: User,
    background_tasks: BackgroundTasks,
) -> Deployment:
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app or app.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    source = db.query(Deployment).filter(
        Deployment.id == source_deployment_id,
        Deployment.application_id == app_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Deployment not found")

    previous_id = source.previous_deployment_id
    if not previous_id:
        raise HTTPException(status_code=400, detail="No previous deployment available to rollback to")

    previous = db.query(Deployment).filter(Deployment.id == previous_id).first()
    if not previous:
        raise HTTPException(status_code=400, detail="Previous deployment record not found")
    if previous.status != "success":
        raise HTTPException(status_code=409, detail="Previous deployment was not successful, cannot safely rollback")

    rollback_deployment_record = Deployment(
        application_id=app_id,
        version_id=previous.version_id,
        deployed_by=user.id,
        status="pending",
        started_at=datetime.now(timezone.utc),
        previous_deployment_id=previous.id,
        rollback_of_deployment_id=source.id,
    )
    db.add(rollback_deployment_record)
    db.commit()
    db.refresh(rollback_deployment_record)

    background_tasks.add_task(
        _execute_deployment,
        deployment_id=rollback_deployment_record.id,
        app_name=app.name,
        version_tag=previous.version.version_tag,
        image_name=previous.version.image_name,
        source_deployment_id=source.id,
    )
    return rollback_deployment_record

def get_deployment(db: Session, app_id: UUID, deployment_id: UUID, user: User) -> Deployment:
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app or app.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id, Deployment.application_id == app_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment

def list_deployments(db: Session, app_id: UUID, user: User, skip: int = 0, limit: int = 20) -> list[Deployment]:
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app or app.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    return (
        db.query(Deployment)
        .filter(Deployment.application_id == app_id)
        .order_by(Deployment.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )