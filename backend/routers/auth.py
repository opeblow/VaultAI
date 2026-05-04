from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.schemas.user import UserRegister, UserLogin, UserResponse, Token
from backend.services import register_user, login_user
from backend.utils.rate_limit import auth_limiter

router = APIRouter(tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"description": "User exists"}},
)
def register(user: UserRegister, db: Session = Depends(get_db)):
    return register_user(db, user)


@router.post(
    "/login",
    response_model=Token,
    responses={401: {"description": "Invalid credentials"}},
    dependencies=[Depends(auth_limiter)],
)
def login(user: UserLogin, db: Session = Depends(get_db)):
    return login_user(db, user)


@router.post(
    "/logout",
    response_model=dict,
    dependencies=[Depends(get_current_user)],
    openapi_extra={"security": [{"BearerAuth": []}]},
)
def logout():
    return {"message": "Successfully logged out"}
