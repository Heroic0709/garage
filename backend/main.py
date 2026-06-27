"""
停车场管控系统 — FastAPI 入口

启动方式:
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

    或在项目根目录:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

访问:
    Swagger UI: http://localhost:8000/docs
    ReDoc:      http://localhost:8000/redoc
"""

import sys
import os

# 确保项目根目录在 sys.path 中（用于导入 main.py 中的 PlateRecognizer）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import entry, payment, exit, admin, auth, blacklist, membership, wallet

app = FastAPI(
    title="停车场管控系统",
    description="基于车牌识别的停车场管控系统 API，支持入场、缴费、出场全流程管理",
    version="1.0.0",
)

# CORS 配置：允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(auth.router, prefix="/api")
app.include_router(blacklist.router, prefix="/api")
app.include_router(membership.router, prefix="/api")
app.include_router(wallet.router, prefix="/api")
app.include_router(entry.router, prefix="/api")
app.include_router(payment.router, prefix="/api")
app.include_router(exit.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "停车场管控系统",
        "version": "1.0.0",
        "docs": "/docs",
    }
