"""
缴费接口
GET  /api/payment/query?plate=xxx  查询待缴费信息
POST /api/payment/pay              执行缴费

流程:
1. 查询指定车牌 status='parking' 的最新记录
2. 计算应缴金额（服务端重新计算，不信任前端）
3. 缴费后创建 payment_record，更新 parking_record.status='paid'
4. 返回缴费信息（含 expire_time）
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.config import PAYMENT_EXPIRE_MINUTES
from backend.database import get_db
from backend.models import ParkingRecord, PaymentRecord, User, WalletTransaction
from backend.schemas import PaymentQueryResponse, PayRequest, PayResponse
from backend.services.billing import calculate_fee
from backend.auth import get_current_user

router = APIRouter(tags=["缴费"])


@router.get("/payment/query", response_model=PaymentQueryResponse)
def query_payment(
    plate: str = Query(..., description="车牌号"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """查询停车费用"""
    # 查询最新在场记录
    record = (
        db.query(ParkingRecord)
        .filter(
            ParkingRecord.plate_number == plate,
            ParkingRecord.status == "parking",
        )
        .order_by(ParkingRecord.entry_time.desc())
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"message": "未找到该车辆的停车记录，请确认车牌号正确"},
        )

    # 检查会员状态
    user = db.query(User).filter(User.id == current_user.id).first()
    is_member = user.membership_expire and user.membership_expire > datetime.now() if user else False

    # 计算费用
    park_hours, amount = calculate_fee(record.entry_time, is_member=is_member)

    return PaymentQueryResponse(
        plate_number=record.plate_number,
        entry_time=record.entry_time,
        park_hours=park_hours,
        amount=amount,
    )


@router.post("/payment/pay", response_model=PayResponse)
def pay_fee(
    req: PayRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """确认缴费"""
    plate_number = req.plate_number

    # 查询最新在场记录
    record = (
        db.query(ParkingRecord)
        .filter(
            ParkingRecord.plate_number == plate_number,
            ParkingRecord.status == "parking",
        )
        .order_by(ParkingRecord.entry_time.desc())
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"message": "未找到该车辆的停车记录，请确认车牌号正确"},
        )

    # 会员费率
    user = db.query(User).filter(User.id == current_user.id).first()
    is_member = user.membership_expire and user.membership_expire > datetime.now() if user else False

    # 服务端重新计算费用（不信任前端传的金额）
    park_hours, amount = calculate_fee(record.entry_time, is_member=is_member)

    # 检查钱包余额
    balance = float(user.wallet_balance)
    if balance < amount:
        raise HTTPException(status_code=400, detail={"message": f"钱包余额不足，需 {amount:.2f} 元，当前余额 {balance:.2f} 元，请先充值"})

    # 扣款
    new_balance = round(balance - amount, 2)
    user.wallet_balance = new_balance

    now = datetime.now()
    expire_time = now + timedelta(minutes=PAYMENT_EXPIRE_MINUTES)

    # 创建缴费记录
    payment = PaymentRecord(
        parking_record_id=record.id,
        plate_number=plate_number,
        amount=amount,
        park_hours=park_hours,
        status="valid",
        pay_time=now,
    )
    db.add(payment)

    # 记录钱包流水
    tx = WalletTransaction(user_id=user.id, type="payment", amount=-amount, balance_after=new_balance, related_id=record.id)
    db.add(tx)

    # 更新停车记录状态
    record.status = "paid"
    db.commit()
    db.refresh(payment)

    return PayResponse(
        amount=float(amount),
        park_hours=park_hours,
        pay_time=now,
        expire_minutes=PAYMENT_EXPIRE_MINUTES,
        expire_time=expire_time,
        message=f"缴费成功，请在 {PAYMENT_EXPIRE_MINUTES} 分钟内出场",
    )
