"""
会员系统
GET  /api/membership/status    查询当前用户会员状态
POST /api/membership/activate  开通/续费会员
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config import MEMBER_MONTHLY_FEE, MEMBER_DAYS, MEMBER_RATE
from backend.database import get_db
from backend.models import User, WalletTransaction

router = APIRouter(tags=["会员"])


@router.get("/membership/status")
def membership_status(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()
    is_member = user.membership_expire and user.membership_expire > datetime.now()
    return {
        "is_member": is_member,
        "expire_at": user.membership_expire.isoformat() if user.membership_expire else None,
        "monthly_fee": MEMBER_MONTHLY_FEE,
        "member_rate": MEMBER_RATE,
    }


@router.post("/membership/activate")
def activate_membership(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()

    balance = float(user.wallet_balance)
    if balance < MEMBER_MONTHLY_FEE:
        raise HTTPException(status_code=400, detail=f"余额不足，需要 {MEMBER_MONTHLY_FEE} 元，当前余额 {balance:.2f} 元")

    new_balance = round(balance - MEMBER_MONTHLY_FEE, 2)
    user.wallet_balance = new_balance

    # 记录钱包流水
    tx = WalletTransaction(user_id=user.id, type="payment", amount=-MEMBER_MONTHLY_FEE, balance_after=new_balance)
    db.add(tx)

    now = datetime.now()
    if user.membership_expire and user.membership_expire > now:
        # 续费：在现有到期时间基础上延长
        user.membership_expire = user.membership_expire + timedelta(days=MEMBER_DAYS)
    else:
        # 新开通
        user.membership_expire = now + timedelta(days=MEMBER_DAYS)

    db.commit()
    return {
        "message": "开通成功",
        "expire_at": user.membership_expire.isoformat(),
        "balance": float(user.wallet_balance),
    }
