"""
计费服务
严格遵循 需求说明文档.md v1.2 的计费规则

规则：
- 首小时 5 元，之后每小时 3 元
- 无免费时段，不满 1 小时按 1 小时计算（向上取整）
- 无封顶
- 方案B：缴费过期后从原始入场时间重新计费，抵扣已缴金额

核心方法:
    calculate_fee(entry_time, exit_time=None) -> (park_hours, amount)
    calculate_deduction(db, parking_record_id) -> float
"""

import math
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.config import FIRST_HOUR_RATE, SUBSEQUENT_HOUR_RATE, MEMBER_RATE


def _calc_hours(entry_time: datetime, exit_time: datetime) -> int:
    """
    计算计费小时数（向上取整，不满1小时按1小时）

    参数:
        entry_time: 入场时间
        exit_time: 出场时间

    返回:
        计费小时数，最小为 1
    """
    delta: timedelta = exit_time - entry_time
    total_minutes = delta.total_seconds() / 60.0
    if total_minutes <= 0:
        return 1
    return math.ceil(total_minutes / 60.0)


def calculate_fee(
    entry_time: datetime,
    exit_time: Optional[datetime] = None,
    is_member: bool = False,
) -> Tuple[int, float]:
    """
    计算停车费用

    公式:
        park_hours = max(1, ceil(elapsed_minutes / 60))
        会员: amount = max(MEMBER_RATE, park_hours * MEMBER_RATE)
        非会员: 首小时 FIRST_HOUR_RATE，之后每小时 SUBSEQUENT_HOUR_RATE

    参数:
        entry_time: 入场时间
        exit_time: 出场时间，默认 None 则用当前时间
        is_member: 是否为会员

    返回:
        (park_hours: int, amount: float)
    """
    if exit_time is None:
        exit_time = datetime.now()

    park_hours = _calc_hours(entry_time, exit_time)

    if is_member:
        amount = max(float(MEMBER_RATE), park_hours * float(MEMBER_RATE))
    elif park_hours <= 1:
        amount = float(FIRST_HOUR_RATE)
    else:
        amount = float(
            FIRST_HOUR_RATE + (park_hours - 1) * SUBSEQUENT_HOUR_RATE
        )

    return park_hours, amount


def calculate_deduction(db: Session, parking_record_id: int) -> float:
    """
    方案B：查询指定停车记录下所有过期缴费的总金额，用于抵扣

    参数:
        db: 数据库会话
        parking_record_id: 停车记录 ID

    返回:
        可抵扣总额（float），无过期缴费则返回 0.0
    """
    from backend.models import PaymentRecord

    result = db.query(func.coalesce(func.sum(PaymentRecord.amount), 0)).filter(
        PaymentRecord.parking_record_id == parking_record_id,
        PaymentRecord.status == "expired"
    ).scalar()

    return float(result)
