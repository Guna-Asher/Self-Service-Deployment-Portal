from uuid import UUID

from app.models.deployment_log import DeploymentLog

def add_log(db, deployment_id: UUID, message: str, level: str = "info"):
    log = DeploymentLog(
        deployment_id=deployment_id,
        message=message,
        level=level,
    )
    db.add(log)
    # No commit here – caller commits