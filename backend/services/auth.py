from sqlalchemy.orm import Session

from models.user import User
from schemas.user import UserRegister, UserLogin, Token, UserResponse
from utils.security import hash_password, verify_password, create_access_token


def register_user(db: Session, user: UserRegister) -> UserResponse:
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        plan=new_user.plan,
        created_at=new_user.created_at,
    )


def login_user(db: Session, user: UserLogin) -> Token:
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": db_user.email})
    return Token(access_token=access_token, token_type="bearer")


def logout_user() -> dict:
    return {"message": "Successfully logged out"}
