"""
JWT 认证工具模块
- 生成/验证 JWT token
- FastAPI 依赖注入：获取当前用户、管理员权限检查
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.hash import bcrypt as bcrypt_hash
from sqlalchemy.orm import Session

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS
from backend.database import get_db

# --- 密码哈希 ---
pwd_context = None  # kept for reference, use verify/hash_password below


def hash_password(password: str) -> str:
    return bcrypt_hash.using(rounds=12).hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt_hash.verify(plain, hashed)

# --- OAuth2 scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def create_access_token(user_id: int, role: str, username: str) -> str:
    """生成 JWT token，默认 7 天有效"""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "username": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """验证 token，返回 payload；失败抛出 401"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
        )


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """FastAPI Depends: 从 Header 解析 token，查询 User 对象"""
    from backend.models import User

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )
    payload = verify_token(token)
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.is_active == 1).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    return user


def require_admin(current_user=Depends(get_current_user)):
    """FastAPI Depends: 仅允许 admin 角色"""
    from backend.models import User

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可执行此操作",
        )
    return current_user
