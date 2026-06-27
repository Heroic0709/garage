"""
Pydantic 请求/响应模型
严格遵循 需求说明文档.md v1.2 的 API 接口设计

包含 8 个 Schema：
- RecognizeResponse      识别结果
- EntryResponse           入场成功
- PaymentQueryResponse    缴费查询
- PayRequest              缴费请求
- PayResponse             缴费成功
- ExitResponse            出场结果
- RecordItem              单条停车记录
- RecordListResponse      记录列表（分页）
- StatisticsResponse      收费统计
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================
# 手动入场 / 出场请求
# ============================================================

class ManualPlateRequest(BaseModel):
    """手动输入车牌号请求"""
    plate_number: str = Field(description="车牌号")


# ============================================================
# 车牌识别
# ============================================================

class RecognizeResponse(BaseModel):
    """车牌识别结果"""
    plate: str = Field(default="", description="车牌号")
    confidence: float = Field(default=0.0, description="置信度")
    success: bool = Field(default=False, description="是否识别成功")

    class Config:
        from_attributes = True


# ============================================================
# Phase 2 认证
# ============================================================

class AuthRegisterRequest(BaseModel):
    username: str = Field(description="用户名", min_length=2, max_length=50)
    password: str = Field(description="密码", min_length=6, max_length=100)


class AuthLoginRequest(BaseModel):
    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class UserInfo(BaseModel):
    id: int
    username: str
    role: str
    phone: Optional[str] = None
    membership_expire: Optional[datetime] = None
    wallet_balance: float = 0.0

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: str = Field(description="JWT token")
    user: UserInfo = Field(description="用户信息")


# ============================================================
# Phase 2 黑名单
# ============================================================

class BlacklistCreateRequest(BaseModel):
    plate_number: str = Field(description="车牌号", min_length=2, max_length=20)
    reason: str = Field(description="拉黑原因", max_length=255)
    black_type: str = Field(default="permanent", description="类型: permanent/temporary")
    expire_days: Optional[int] = Field(default=None, description="限时天数（仅 temporary）")


class BlacklistItem(BaseModel):
    id: int
    plate_number: str
    reason: str
    black_type: str
    expire_at: Optional[datetime] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BlacklistListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[BlacklistItem]


class RecognizeOnlyResponse(BaseModel):
    """仅识别不入库 — 返回给前端确认"""
    plate_number: str = Field(description="识别到的车牌号")
    confidence: float = Field(description="识别置信度")
    image_path: str = Field(default="", description="保存的图片路径")

    class Config:
        from_attributes = True


# ============================================================
# 入场
# ============================================================

class EntryResponse(BaseModel):
    """入场成功响应"""
    id: int = Field(description="停车记录 ID")
    plate_number: str = Field(description="车牌号")
    entry_time: datetime = Field(description="入场时间")
    status: str = Field(default="parking", description="状态")

    class Config:
        from_attributes = True


# ============================================================
# 缴费查询
# ============================================================

class PaymentQueryResponse(BaseModel):
    """缴费查询响应"""
    plate_number: str = Field(description="车牌号")
    entry_time: datetime = Field(description="入场时间")
    park_hours: int = Field(description="计费小时数")
    amount: float = Field(description="应付金额（元）")

    class Config:
        from_attributes = True


# ============================================================
# 确认缴费
# ============================================================

class PayRequest(BaseModel):
    """缴费请求"""
    plate_number: str = Field(description="车牌号")


class PayResponse(BaseModel):
    """缴费成功响应"""
    amount: float = Field(description="缴费金额（元）")
    park_hours: int = Field(description="计费小时数")
    pay_time: datetime = Field(description="缴费时间")
    expire_minutes: int = Field(description="有效期限（分钟）")
    expire_time: datetime = Field(description="过期时间")
    message: str = Field(default="缴费成功，请在 20 分钟内出场", description="提示信息")

    class Config:
        from_attributes = True


# ============================================================
# 出场
# ============================================================

class ExitResponse(BaseModel):
    """出场校验响应"""
    plate_number: str = Field(default="", description="车牌号")
    can_exit: bool = Field(default=False, description="是否可以出场")
    reason: Optional[str] = Field(
        default=None,
        description="不可出场原因：no_record / not_paid / expired"
    )
    total_amount: Optional[float] = Field(
        default=None,
        description="过期场景：当前总费用"
    )
    paid_amount: Optional[float] = Field(
        default=None,
        description="过期场景：已缴可抵扣金额"
    )
    need_pay: Optional[float] = Field(
        default=None,
        description="过期场景：需补缴金额"
    )
    message: str = Field(default="", description="提示信息")

    class Config:
        from_attributes = True


# ============================================================
# 管理后台
# ============================================================

class RecordItem(BaseModel):
    """单条停车记录（列表用）"""
    id: int
    plate_number: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    status: str
    paid_amount: float = 0.0

    class Config:
        from_attributes = True


class RecordListResponse(BaseModel):
    """停车记录列表（分页）"""
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    items: List[RecordItem] = Field(default_factory=list, description="记录列表")


class StatisticsResponse(BaseModel):
    """收费统计"""
    today_income: float = Field(default=0.0, description="今日收入（元）")
    month_income: float = Field(default=0.0, description="本月收入（元）")
    total_income: float = Field(default=0.0, description="总收入（元）")
    parked_count: int = Field(default=0, description="当前在场车辆数")

    class Config:
        from_attributes = True
