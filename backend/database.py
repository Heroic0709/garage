"""
数据库连接配置
严格遵循 数据库设计文档.md v1.2 的连接信息

连接参数:
    Host: localhost
    Port: 3306
    User: root
    Password: 123456
    Database: parking_system
    Charset: utf8mb4
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ============================================================
# 数据库连接 URL
# 格式: mysql+pymysql://user:password@host:port/database?charset=utf8mb4
# ============================================================
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/parking_system?charset=utf8mb4"

# ============================================================
# 创建引擎
# pool_pre_ping=True: 每次从连接池取出连接时先 ping，确保连接有效
# pool_recycle=3600: 连接存活 1 小时后回收，避免 MySQL 默认 8 小时超时断开
# ============================================================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,  # 生产环境关闭 SQL 日志
)

# ============================================================
# 会话工厂
# autocommit=False: 手动控制事务
# autoflush=False: 手动控制 flush
# ============================================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """
    FastAPI 依赖注入函数，每个请求获取独立的数据库会话，
    请求结束后自动关闭释放连接。
    
    使用方式:
        @app.get("/xxx")
        def handler(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
