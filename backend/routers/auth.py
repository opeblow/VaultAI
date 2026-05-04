from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.auth import get_password_hash, verify_password, create_access_token, get_current_user
from backend.models.schemas import RefreshToken, User
from backend.models.schemas import (
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    TokenResponse,
    ErrorResponse,
    UserResponse,
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


REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_refresh_token_record(user_id: int, db: Session) -> str:
    token = secrets.token_urlsafe(48)
    db.add(
        RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            revoked="false",
        )
    )
    return token


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
    refresh_token = create_refresh_token_record(user.id, db)
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh an access token",
    description="Issues a new short-lived JWT access token for a valid refresh token."
)
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == request.refresh_token
    ).first()

    if (
        refresh_token is None
        or refresh_token.revoked == "true"
        or refresh_token.expires_at < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.id == refresh_token.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token = create_access_token(data={"sub": user.email})
    return RefreshTokenResponse(access_token=access_token)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and revoke refresh token",
    description="Revokes a refresh token so it can no longer mint access tokens."
)
def logout(request: LogoutRequest, db: Session = Depends(get_db)):
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == request.refresh_token
    ).first()

    if refresh_token is not None:
        refresh_token.revoked = "true"
        db.commit()

    return LogoutResponse()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the authenticated user's profile."
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
