import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, UUID
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    plan = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    payments = relationship("Payment", back_populates="user")
