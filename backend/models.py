"""
数据库模型定义
严格遵循 数据库设计文档.md v1.2

表结构：
- parking_record: 停车记录表，记录车辆从入场到出场的完整生命周期
- payment_record: 缴费记录表，记录每一笔缴费明细
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, DECIMAL, ForeignKey, Index, func
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class ParkingRecord(Base):
    """停车记录表 - 对应数据库 parking_record"""
    __tablename__ = "parking_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    plate_number = Column(
        String(20), nullable=False, index=True,
        comment="车牌号（如豫B·60P70）"
    )
    plate_image = Column(
        String(500), nullable=True,
        comment="入场车牌图片的存储路径"
    )
    entry_time = Column(
        DateTime, nullable=False, index=True,
        comment="入场时间"
    )
    exit_time = Column(
        DateTime, nullable=True,
        comment="出场时间（在场时为空）"
    )
    status = Column(
        String(20), nullable=False, default="parking", index=True,
        comment="状态：parking-在场 / paid-已缴费 / exited-已出场"
    )
    created_at = Column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        comment="记录创建时间"
    )

    # 关联 payment_record，一条停车记录可有多笔缴费
    payments = relationship(
        "PaymentRecord", back_populates="parking_record",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<ParkingRecord(id={self.id}, plate='{self.plate_number}', "
            f"status='{self.status}')>"
        )


class PaymentRecord(Base):
    """缴费记录表 - 对应数据库 payment_record"""
    __tablename__ = "payment_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    parking_record_id = Column(
        Integer,
        ForeignKey("parking_record.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False, index=True,
        comment="关联停车记录ID"
    )
    plate_number = Column(
        String(20), nullable=False, index=True,
        comment="车牌号（冗余，便于直接查询）"
    )
    amount = Column(
        DECIMAL(10, 2), nullable=False,
        comment="缴费金额（元）"
    )
    park_hours = Column(
        Integer, nullable=False,
        comment="计费小时数（向上取整）"
    )
    status = Column(
        String(20), nullable=False, default="valid",
        comment="状态：valid-有效 / expired-已过期"
    )
    pay_time = Column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        comment="缴费时间"
    )

    # 反向关联
    parking_record = relationship("ParkingRecord", back_populates="payments")

    def __repr__(self):
        return (
            f"<PaymentRecord(id={self.id}, plate='{self.plate_number}', "
            f"amount={self.amount}, status='{self.status}')>"
        )


# ============================================================
# Phase 2

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    phone = Column(String(20), nullable=True)
    membership_expire = Column(DateTime, nullable=True)
    wallet_balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

class UserCar(Base):
    __tablename__ = "user_cars"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plate_number = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())


class WalletTransaction(Base):
    __tablename__ = "wallet_transaction"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    balance_after = Column(DECIMAL(10, 2), nullable=False)
    related_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())


class Blacklist(Base):
    __tablename__ = "blacklist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_number = Column(String(20), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    black_type = Column(String(20), nullable=False, default="permanent")
    expire_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

# Index 注解说明（已在 Column 中通过 index=True 定义）
# MySQL 中已存在的索引与模型定义一致：
#
# parking_record:
#   PRIMARY (id)
#   idx_plate_number (plate_number)
#   idx_status (status)
#   idx_entry_time (entry_time)
#
# payment_record:
#   PRIMARY (id)
#   idx_parking_record_id (parking_record_id)
#   idx_plate_number (plate_number)
#   idx_pay_time (pay_time)
#   fk_payment_parking (parking_record_id) → parking_record.id
# ============================================================
