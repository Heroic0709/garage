"""
auth: register / login / me
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import hash_password, verify_password, create_access_token, get_current_user
from backend.database import get_db
from backend.models import User
from backend.schemas import AuthRegisterRequest, AuthLoginRequest, AuthResponse, UserInfo

router = APIRouter(tags=["认证"])


@router.post("/auth/register", response_model=AuthResponse)
def register(body: AuthRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.role, user.username)
    return AuthResponse(token=token, user=UserInfo.model_validate(user))


@router.post("/auth/login", response_model=AuthResponse)
def login(body: AuthLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username, User.is_active == 1).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.id, user.role, user.username)
    return AuthResponse(token=token, user=UserInfo.model_validate(user))


@router.get("/auth/me", response_model=UserInfo)
def get_me(current_user: User = Depends(get_current_user)):
    return UserInfo.model_validate(current_user)
