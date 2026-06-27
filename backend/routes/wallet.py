"""
钱包接口
GET   /api/wallet/balance      查询余额
POST  /api/wallet/recharge     充值
GET   /api/wallet/transactions  交易流水
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User, WalletTransaction

router = APIRouter(tags=["钱包"])


@router.get("/wallet/balance")
def get_balance(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()
    return {"balance": float(user.wallet_balance)}


@router.post("/wallet/recharge")
def recharge(body: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    amount = float(body.get("amount", 0))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="充值金额必须大于0")
    user = db.query(User).filter(User.id == current_user.id).first()
    new_balance = round(float(user.wallet_balance) + amount, 2)
    user.wallet_balance = new_balance
    tx = WalletTransaction(user_id=user.id, type="recharge", amount=amount, balance_after=new_balance)
    db.add(tx)
    db.commit()
    return {"message": "充值成功", "balance": new_balance}


@router.get("/wallet/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(WalletTransaction).filter(WalletTransaction.user_id == current_user.id)
    total = query.count()
    rows = query.order_by(WalletTransaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": r.id,
            "type": r.type,
            "amount": float(r.amount),
            "balance_after": float(r.balance_after),
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
    return {"total": total, "page": page, "page_size": page_size, "items": items}
