from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.user import User
from app.schemas.application import ApplicationCreate

def create_application(db: Session, payload: ApplicationCreate, owner: User) -> Application:
    if db.query(Application).filter(Application.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Application name already exists")
    app = Application(
        name=payload.name,
        description=payload.description,
        repository_url=str(payload.repository_url) if payload.repository_url else None,
        owner_id=owner.id,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

def list_applications(db: Session, owner: User) -> list[Application]:
    return db.query(Application).filter(Application.owner_id == owner.id).order_by(Application.created_at.desc()).all()

def get_application(db: Session, app_id: UUID, owner: User) -> Application:
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.owner_id != owner.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this application")
    return app

def delete_application(db: Session, app_id: UUID, owner: User) -> dict:
    app = get_application(db, app_id, owner)
    db.delete(app)
    db.commit()
    return {"detail": f"Application '{app.name}' deleted successfully"}