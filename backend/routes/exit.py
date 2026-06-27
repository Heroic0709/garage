"""
出场接口
POST /api/exit

流程:
1. 上传出场图片，识别车牌
2. 查询该车牌最新在场记录
3. 根据状态处理:
   - parking: 提示未缴费
   - paid + 在有效期内: 放行
   - paid + 已过期: 方案B — 回退状态、标记过期、计算抵扣、提示补缴
   - exited: 已出场
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.config import PAYMENT_EXPIRE_MINUTES
from backend.database import get_db
from backend.models import ParkingRecord, PaymentRecord, User
from backend.schemas import ExitResponse, ManualPlateRequest
from backend.services.billing import calculate_fee, calculate_deduction
from backend.services.plate_service import recognize_and_save
from backend.auth import get_current_user

router = APIRouter(tags=["出场"])


@router.post("/exit", response_model=ExitResponse)
async def exit_car(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    车辆出场

    - 上传车牌图片，自动识别
    - 校验缴费状态和有效期
    - 有效期内 → 放行
    - 已过期 → 方案B：抵扣已缴金额，提示需补缴差额
    """
    # 检查会员状态
    user = db.query(User).filter(User.id == current_user.id).first()
    is_member = user.membership_expire and user.membership_expire > datetime.now() if user else False
    # 1. 识别车牌
    result = await recognize_and_save(image)
    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "error": result["error"],
                "message": "车牌识别失败，请重试",
            },
        )

    plate_number = result["plate_number"]

    # 2. 查询最新在场记录
    record = (
        db.query(ParkingRecord)
        .filter(
            ParkingRecord.plate_number == plate_number,
            ParkingRecord.status.in_(["parking", "paid"]),
        )
        .order_by(ParkingRecord.entry_time.desc())
        .first()
    )

    if not record:
        return ExitResponse(
            plate_number=plate_number,
            can_exit=False,
            reason="no_record",
            message="未找到入场记录",
        )

    # 3. 未缴费 → 提示先缴费
    if record.status == "parking":
        # 实时计算当前费用提示用户
        park_hours, amount = calculate_fee(record.entry_time, is_member=is_member)
        return ExitResponse(
            plate_number=plate_number,
            can_exit=False,
            reason="not_paid",
            total_amount=amount,
            message=f"请先缴费，当前应缴 {amount:.2f} 元",
        )

    # 4. 已缴费 → 校验有效期
    if record.status == "paid":
        # 查找该记录下最近一笔有效缴费
        latest_payment = (
            db.query(PaymentRecord)
            .filter(
                PaymentRecord.parking_record_id == record.id,
                PaymentRecord.status == "valid",
            )
            .order_by(PaymentRecord.pay_time.desc())
            .first()
        )

        if not latest_payment:
            # 异常情况：paid 状态但没有 valid 缴费记录，回退为 parking
            record.status = "parking"
            db.commit()
            return ExitResponse(
                plate_number=plate_number,
                can_exit=False,
                reason="not_paid",
                message="请先缴费",
            )

        pay_time = latest_payment.pay_time
        expire_deadline = pay_time + timedelta(minutes=PAYMENT_EXPIRE_MINUTES)
        now = datetime.now()

        # 4a. 在有效期内 → 放行
        if now <= expire_deadline:
            record.exit_time = now
            record.status = "exited"
            db.commit()
            return ExitResponse(
                plate_number=plate_number,
                can_exit=True,
                message="已缴费，请通行",
            )

        # 4b. 已过期 → 方案B：抵扣补缴
        # Step 1: 标记旧缴费为 expired
        latest_payment.status = "expired"

        # Step 2: parking_record 回退为 parking
        record.status = "parking"

        # Step 3: 从原始 entry_time 重新计算总费用
        park_hours, total_amount = calculate_fee(record.entry_time, now, is_member=is_member)

        # Step 4: 计算可抵扣金额（该记录下所有 expired 的缴费）
        paid_amount = calculate_deduction(db, record.id)

        need_pay = round(total_amount - paid_amount, 2)
        if need_pay < 0:
            need_pay = 0.0

        db.commit()

        return ExitResponse(
            plate_number=plate_number,
            can_exit=False,
            reason="expired",
            total_amount=total_amount,
            paid_amount=paid_amount,
            need_pay=need_pay,
            message=f"缴费已过期，需补缴 {need_pay:.2f} 元",
        )

    # 5. 兜底
    return ExitResponse(
        plate_number=plate_number,
        can_exit=False,
        reason="unknown",
        message="未知状态，请联系管理员",
    )


@router.post("/exit/manual", response_model=ExitResponse)
async def exit_car_manual(
    req: ManualPlateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """车辆出场（手动输入车牌号）"""
    # 检查会员状态
    user = db.query(User).filter(User.id == current_user.id).first()
    is_member = user.membership_expire and user.membership_expire > datetime.now() if user else False

    plate_number = req.plate_number

    # 查询最新在场记录
    record = (
        db.query(ParkingRecord)
        .filter(
            ParkingRecord.plate_number == plate_number,
            ParkingRecord.status.in_(["parking", "paid"]),
        )
        .order_by(ParkingRecord.entry_time.desc())
        .first()
    )

    if not record:
        return ExitResponse(
            plate_number=plate_number,
            can_exit=False,
            reason="no_record",
            message="未找到入场记录",
        )

    # 未缴费
    if record.status == "parking":
        park_hours, amount = calculate_fee(record.entry_time, is_member=is_member)
        return ExitResponse(
            plate_number=plate_number,
            can_exit=False,
            reason="not_paid",
            total_amount=amount,
            message=f"请先缴费，当前应缴 {amount:.2f} 元",
        )

    # 已缴费 → 校验有效期
    if record.status == "paid":
        latest_payment = (
            db.query(PaymentRecord)
            .filter(
                PaymentRecord.parking_record_id == record.id,
                PaymentRecord.status == "valid",
            )
            .order_by(PaymentRecord.pay_time.desc())
            .first()
        )

        if not latest_payment:
            record.status = "parking"
            db.commit()
            return ExitResponse(
                plate_number=plate_number,
                can_exit=False,
                reason="not_paid",
                message="请先缴费",
            )

        pay_time = latest_payment.pay_time
        expire_deadline = pay_time + timedelta(minutes=PAYMENT_EXPIRE_MINUTES)
        now = datetime.now()

        if now <= expire_deadline:
            record.exit_time = now
            record.status = "exited"
            db.commit()
            return ExitResponse(
                plate_number=plate_number,
                can_exit=True,
                message="已缴费，请通行",
            )

        # 过期 → 方案B
        latest_payment.status = "expired"
        record.status = "parking"
        park_hours, total_amount = calculate_fee(record.entry_time, now, is_member=is_member)
        paid_amount = calculate_deduction(db, record.id)
        need_pay = round(total_amount - paid_amount, 2)
        if need_pay < 0:
            need_pay = 0.0
        db.commit()

        return ExitResponse(
            plate_number=plate_number,
            can_exit=False,
            reason="expired",
            total_amount=total_amount,
            paid_amount=paid_amount,
            need_pay=need_pay,
            message=f"缴费已过期，需补缴 {need_pay:.2f} 元",
        )

    return ExitResponse(
        plate_number=plate_number,
        can_exit=False,
        reason="unknown",
        message="未知状态，请联系管理员",
    )
