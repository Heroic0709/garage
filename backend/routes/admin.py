"""
管理后台接口
GET /api/admin/records     停车记录列表（分页+筛选）
GET /api/admin/statistics  收费统计数据
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import ParkingRecord, PaymentRecord, WalletTransaction, User
from backend.schemas import RecordItem, RecordListResponse, StatisticsResponse
from backend.auth import require_admin

router = APIRouter(tags=["管理后台"])


@router.get("/admin/records", response_model=RecordListResponse)
def get_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    status: str = Query(default=None, description="状态筛选: parking/paid/exited"),
    plate: str = Query(default=None, description="车牌号模糊搜索"),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """停车记录列表（分页）

    - 支持按状态筛选
    - 支持按车牌号模糊搜索
    - LEFT JOIN payment_record 获取实缴金额（仅 valid 的缴费）
    """
    # 构建子查询：每条 parking_record 的 valid 缴费总金额
    paid_subq = (
        db.query(
            PaymentRecord.parking_record_id,
            func.coalesce(func.sum(PaymentRecord.amount), 0).label("paid_amount"),
        )
        .filter(PaymentRecord.status == "valid")
        .group_by(PaymentRecord.parking_record_id)
        .subquery()
    )

    # 主查询
    query = db.query(
        ParkingRecord,
        func.coalesce(paid_subq.c.paid_amount, 0).label("paid_amount"),
    ).outerjoin(
        paid_subq,
        ParkingRecord.id == paid_subq.c.parking_record_id,
    )

    # 筛选条件
    if status:
        query = query.filter(ParkingRecord.status == status)
    if plate:
        query = query.filter(ParkingRecord.plate_number.contains(plate))

    # 总数
    total = query.count()

    # 分页 + 排序
    rows = (
        query
        .order_by(ParkingRecord.entry_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        RecordItem(
            id=r.ParkingRecord.id,
            plate_number=r.ParkingRecord.plate_number,
            entry_time=r.ParkingRecord.entry_time,
            exit_time=r.ParkingRecord.exit_time,
            status=r.ParkingRecord.status,
            paid_amount=float(r.paid_amount),
        )
        for r in rows
    ]

    return RecordListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/admin/statistics", response_model=StatisticsResponse)
def get_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """收费统计数据"""
    today = date.today()

    # 今日收入（停车缴费 + 会员消费）
    today_parking = db.query(func.coalesce(func.sum(PaymentRecord.amount), 0)).filter(
        func.date(PaymentRecord.pay_time) == today, PaymentRecord.status == "valid"
    ).scalar()
    today_wallet = db.query(func.coalesce(func.sum(WalletTransaction.amount), 0)).filter(
        func.date(WalletTransaction.created_at) == today,
        WalletTransaction.type == "payment",
    ).scalar()
    today_income = round(float(today_parking) + abs(float(today_wallet)), 2)

    # 本月收入
    month_parking = db.query(func.coalesce(func.sum(PaymentRecord.amount), 0)).filter(
        func.year(PaymentRecord.pay_time) == today.year,
        func.month(PaymentRecord.pay_time) == today.month,
        PaymentRecord.status == "valid",
    ).scalar()
    month_wallet = db.query(func.coalesce(func.sum(WalletTransaction.amount), 0)).filter(
        func.year(WalletTransaction.created_at) == today.year,
        func.month(WalletTransaction.created_at) == today.month,
        WalletTransaction.type == "payment",
    ).scalar()
    month_income = round(float(month_parking) + abs(float(month_wallet)), 2)

    # 总收入
    total_parking = db.query(func.coalesce(func.sum(PaymentRecord.amount), 0)).filter(
        PaymentRecord.status == "valid",
    ).scalar()
    total_wallet = db.query(func.coalesce(func.sum(WalletTransaction.amount), 0)).filter(
        WalletTransaction.type == "payment",
    ).scalar()
    total_income = round(float(total_parking) + abs(float(total_wallet)), 2)

    # 当前在场车辆数
    parked_count = db.query(func.count(ParkingRecord.id)).filter(
        ParkingRecord.status.in_(["parking", "paid"])
    ).scalar()

    return StatisticsResponse(
        today_income=float(today_income),
        month_income=float(month_income),
        total_income=float(total_income),
        parked_count=parked_count,
    )


@router.get("/admin/consumption")
def get_consumption(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """会员消费记录（wallet_transaction type=payment）"""
    query = (
        db.query(WalletTransaction, User.username)
        .join(User, WalletTransaction.user_id == User.id)
        .filter(WalletTransaction.type == "payment")
    )
    total = query.count()
    rows = query.order_by(WalletTransaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": tx.id,
            "username": username,
            "amount": abs(float(tx.amount)),
            "balance_after": float(tx.balance_after),
            "created_at": tx.created_at.isoformat(),
        }
        for tx, username in rows
    ]
    return {"total": total, "page": page, "page_size": page_size, "items": items}
