"""
系统配置
集中管理所有可配置参数
严格遵循 需求说明文档.md v1.2 的计费规则
"""

import os

# ============================================================
# 计费配置
# ============================================================
FIRST_HOUR_RATE = 5          # 首小时费率（元）
SUBSEQUENT_HOUR_RATE = 3     # 后续每小时费率（元）

# ============================================================
# 缴费有效期
# ============================================================
PAYMENT_EXPIRE_MINUTES = 20  # 缴费成功后有效期限（分钟），可配置

# ============================================================
# 文件上传
# ============================================================
# 上传图片存储目录（相对于项目根目录）
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "uploads"
)

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

# JWT
SECRET_KEY = "parking-system-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# member
MEMBER_RATE = 3
MEMBER_MONTHLY_FEE = 20
MEMBER_DAYS = 30
