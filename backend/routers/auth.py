"""
VaultAI Authentication Router

This module provides authentication endpoints for user registration and login.
Implements JWT-based authentication with bcrypt password hashing.
"""

import os
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.auth import get_password_hash, verify_password, create_access_token, get_current_user
from backend.models.schemas import User
from backend.models.schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    TokenResponse,
    ErrorResponse
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Conflict - User already exists"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with the provided name, email, and password. Password is securely hashed using bcrypt."
)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    user = User(
        name=request.name,
        email=request.email,
        password_hash=get_password_hash(request.password),
        plan="free"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserRegisterResponse(
        user_id=user.id,
        email=user.email,
        message="User registered successfully"
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access token",
    description="Authenticates a user with email and password, returns a JWT access token."
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )