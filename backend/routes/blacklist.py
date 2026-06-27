"""
黑名单管理
GET    /api/blacklist          查询黑名单列表
POST   /api/blacklist/add      添加黑名单
DELETE /api/blacklist/remove   移除黑名单
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.auth import get_current_user, require_admin
from backend.database import get_db
from backend.models import Blacklist
from backend.schemas import BlacklistCreateRequest, BlacklistItem, BlacklistListResponse

router = APIRouter(tags=["黑名单"])


@router.get("/blacklist", response_model=BlacklistListResponse)
def list_blacklist(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str = Query(default=None, description="active/expired/removed"),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Blacklist)
    if status:
        query = query.filter(Blacklist.status == status)
    total = query.count()
    rows = query.order_by(Blacklist.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [BlacklistItem.model_validate(r) for r in rows]
    return BlacklistListResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("/blacklist/add")
def add_blacklist(
    body: BlacklistCreateRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    # check duplicate
    existing = db.query(Blacklist).filter(
        Blacklist.plate_number == body.plate_number,
        Blacklist.status == "active",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该车牌已在黑名单中")

    expire_at = None
    if body.black_type == "temporary" and body.expire_days:
        expire_at = datetime.now() + timedelta(days=body.expire_days)

    bl = Blacklist(
        plate_number=body.plate_number,
        reason=body.reason,
        black_type=body.black_type,
        expire_at=expire_at,
        status="active",
        created_by=current_user.id,
    )
    db.add(bl)
    db.commit()
    db.refresh(bl)
    return {"message": "添加成功", "id": bl.id}


@router.delete("/blacklist/remove")
def remove_blacklist(
    plate_number: str = Query(..., description="车牌号"),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    bl = db.query(Blacklist).filter(
        Blacklist.plate_number == plate_number,
        Blacklist.status == "active",
    ).first()
    if not bl:
        raise HTTPException(status_code=404, detail="未找到该黑名单记录")
    db.delete(bl)
    db.commit()
    return {"message": "移除成功"}
