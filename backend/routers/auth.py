"""
VaultAI Authentication Router

This module provides authentication endpoints for user registration and login.
Implements JWT-based authentication with bcrypt password hashing.
"""

import os
from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.auth import get_password_hash, verify_password, create_access_token, get_current_user, decode_token
from backend.models.schemas import User, RefreshToken
from backend.models.schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    LogoutResponse,
    ErrorResponse
)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Conflict - User already exists"},
        429: {"model": ErrorResponse, "description": "Too Many Requests"},
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
@limiter.limit("3/minute")
def register(request: UserRegisterRequest, db: Session = Depends(get_db), request_obj: Request = None):
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access token",
    description="Authenticates a user with email and password, returns JWT access and refresh tokens."
)
@limiter.limit("5/minute")
def login(request: UserLoginRequest, db: Session = Depends(get_db), request_obj: Request = None):
    try:
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        refresh_token_expires = datetime.utcnow() + timedelta(days=7)
        refresh_token_str = create_access_token(
            data={"sub": user.email, "type": "refresh"},
            expires_delta=timedelta(days=7)
        )
        
        refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=refresh_token_expires,
            revoked="false"
        )
        db.add(refresh_token)
        db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
    description="Uses a valid refresh token to generate a new access token."
)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(request.refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.token == request.refresh_token,
            RefreshToken.revoked == "false"
        ).first()
        
        if not refresh_token_record or refresh_token_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or revoked"
            )
        
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        access_token_expires = timedelta(minutes=30)
        new_access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            token_type="bearer"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and revoke refresh token",
    description="Revokes the refresh token to log the user out."
)
def logout(request: LogoutRequest, db: Session = Depends(get_db)):
    try:
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.token == request.refresh_token,
            RefreshToken.revoked == "false"
        ).first()
        
        if refresh_token_record:
            refresh_token_record.revoked = "true"
            db.commit()
        
        return LogoutResponse(message="Successfully logged out")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )