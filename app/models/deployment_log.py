import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

def utcnow():
    return datetime.now(timezone.utc)

class DeploymentLog(Base):
    __tablename__ = "deployment_logs"
    __table_args__ = (
        CheckConstraint(
            "level IN ('info','warning','error')",
            name="ck_deployment_log_level",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(20), nullable=False, server_default="info")
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), default=utcnow)

    deployment = relationship("Deployment", back_populates="logs")