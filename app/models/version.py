import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

def utcnow():
    return datetime.now(timezone.utc)

class Version(Base):
    __tablename__ = "versions"
    __table_args__ = (
        UniqueConstraint("application_id", "version_tag", name="uq_app_version_tag"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    version_tag = Column(String(100), nullable=False)
    image_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), default=utcnow)

    application = relationship("Application", back_populates="versions")
    deployments = relationship("Deployment", back_populates="version")