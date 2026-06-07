import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), default=utcnow, onupdate=utcnow)

    applications = relationship("Application", back_populates="owner", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="deployer")

    def __repr__(self):
        return f"<User {self.username}>"