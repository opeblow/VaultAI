"""
VaultAI Database Models

This module defines all SQLAlchemy ORM models for the application.
Models include User, Podcast, Job, and Payment with proper relationships.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
import enum

from backend.database import Base


class PlanEnum(str, enum.Enum):
    FREE = "free"
    CREATOR = "creator"
    STUDIO = "studio"


class JobStatusEnum(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    plan = Column(String(50), default=PlanEnum.FREE.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    podcasts = relationship("Podcast", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")


class Podcast(Base):
    __tablename__ = "podcasts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    language = Column(String(50), default="unknown")
    duration = Column(Float, default=0.0)
    speaker_count = Column(Integer, default=0)
    vault_path = Column(String(1000), nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(50), default=JobStatusEnum.PROCESSING.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="podcasts")
    jobs = relationship("Job", back_populates="podcast", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"), nullable=True, index=True)
    status = Column(String(50), default=JobStatusEnum.PROCESSING.value, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="jobs")
    podcast = relationship("Podcast", back_populates="jobs")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    provider = Column(String(50), default="paystack", nullable=False)
    status = Column(String(50), default=PaymentStatusEnum.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="payments")


from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    email: str
    message: str = "User registered successfully"


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PodcastUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


class PodcastUploadResponse(BaseModel):
    job_id: int
    status: str = "processing"


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    job_id: int
    status: str
    error: Optional[str] = None


class QueryAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    podcast_id: int


class QueryAskResponse(BaseModel):
    answer: str
    podcast_id: int


class PodcastListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    language: str
    speaker_count: int
    summary: Optional[str] = None
    status: str
    created_at: datetime


class PodcastListResponse(BaseModel):
    podcasts: List[PodcastListItem]


class PodcastSummaryResponse(BaseModel):
    summary: Optional[str] = None
    speakers: int
    language: str
    duration: float


class PaymentWebhookRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


class PaymentWebhookResponse(BaseModel):
    message: str = "OK"


class ErrorResponse(BaseModel):
    detail: str


class ValidationErrorResponse(BaseModel):
    detail: List[dict]


class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    message: str = "VaultAI API is running"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: str
    plan: str
    created_at: datetime