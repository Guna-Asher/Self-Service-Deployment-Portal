from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.user import User
from app.models.version import Version
from app.schemas.version import VersionCreate

def _get_application_and_check_ownership(db: Session, app_id: UUID, owner: User) -> Application:
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.owner_id != owner.id:
        raise HTTPException(status_code=403, detail="You do not have permission to manage this application")
    return app

def create_version(db: Session, app_id: UUID, payload: VersionCreate, owner: User) -> Version:
    app = _get_application_and_check_ownership(db, app_id, owner)
    existing = db.query(Version).filter(
        Version.application_id == app_id,
        Version.version_tag == payload.version_tag,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Version tag '{payload.version_tag}' already exists for this application")
    version = Version(
        application_id=app.id,
        version_tag=payload.version_tag,
        image_name=payload.image_name,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version

def list_versions(db: Session, app_id: UUID, owner: User) -> list[Version]:
    _get_application_and_check_ownership(db, app_id, owner)
    return db.query(Version).filter(Version.application_id == app_id).order_by(Version.created_at.desc()).all()

def get_version(db: Session, app_id: UUID, version_id: UUID, owner: User) -> Version:
    _get_application_and_check_ownership(db, app_id, owner)
    version = db.query(Version).filter(Version.id == version_id, Version.application_id == app_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version