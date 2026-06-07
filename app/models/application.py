import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

def utcnow():
    return datetime.now(timezone.utc)

class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    repository_url = Column(String(500), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="applications")
    versions = relationship("Version", back_populates="application", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="application", cascade="all, delete-orphan")