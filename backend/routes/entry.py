"""
入场接口
POST /api/entry

流程:
1. 接收上传的车牌图片
2. 调用车牌识别引擎
3. 校验是否重复入场（同一车牌有 parking/paid 状态记录则拒绝）
4. 创建 parking_record（status='parking'）
5. 返回入场信息
"""

from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ParkingRecord, Blacklist
from backend.schemas import EntryResponse, ManualPlateRequest, RecognizeOnlyResponse
from backend.services.plate_service import recognize_and_save
from backend.auth import get_current_user

router = APIRouter(tags=["入场"])


@router.post("/entry/recognize", response_model=RecognizeOnlyResponse)
async def recognize_plate(
    image: UploadFile = File(...),
    current_user = Depends(get_current_user),
):
    """
    仅识别车牌，不入库

    上传车牌图片，返回识别到的车牌号和置信度。
    前端展示结果让用户确认后，再调用 /entry/manual 完成入场。
    """
    result = await recognize_and_save(image)
    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "error": result["error"],
                "message": "车牌识别失败，请上传清晰的车牌图片或手动输入",
            },
        )
    return RecognizeOnlyResponse(
        plate_number=result["plate_number"],
        confidence=result["confidence"],
        image_path=result["image_path"],
    )


@router.post("/entry", response_model=EntryResponse)
async def entry_car(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    车辆入场

    - 上传车牌图片，自动识别车牌号
    - 识别成功后创建入场记录
    - 同一车牌在场不可重复入场
    """
    # 1. 调用车牌识别
    result = await recognize_and_save(image)
    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "error": result["error"],
                "message": "车牌识别失败，请上传清晰的车牌图片或手动输入",
            },
        )

    plate_number = result["plate_number"]
    image_path = result["image_path"]

    # 2. 检查黑名单
    black = db.query(Blacklist).filter(
        Blacklist.plate_number == plate_number,
        Blacklist.status == "active",
    ).first()
    if black:
        raise HTTPException(
            status_code=403,
            detail={"message": f"该车辆已被列入黑名单，原因：{black.reason}，禁止入场"},
        )

    # 3. 校验重复入场
    existing = (
        db.query(ParkingRecord)
        .filter(
            ParkingRecord.plate_number == plate_number,
            ParkingRecord.status.in_(["parking", "paid"]),
        )
        .order_by(ParkingRecord.entry_time.desc())
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail={"message": f"该车辆已在场内（{existing.status}），不可重复入场"},
        )

    # 4. 创建入场记录
    now = datetime.now()
    record = ParkingRecord(
        plate_number=plate_number,
        plate_image=image_path,
        entry_time=now,
        status="parking",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 4. 返回结果
    return EntryResponse(
        id=record.id,
        plate_number=record.plate_number,
        entry_time=record.entry_time,
        status=record.status,
    )


@router.post("/entry/manual", response_model=EntryResponse)
def entry_car_manual(
    body: ManualPlateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """车辆入场（手动输入车牌号）"""
    plate_number = body.plate_number

    # 检查黑名单
    black = db.query(Blacklist).filter(
        Blacklist.plate_number == plate_number,
        Blacklist.status == "active",
    ).first()
    if black:
        raise HTTPException(
            status_code=403,
            detail={"message": f"该车辆已被列入黑名单，原因：{black.reason}，禁止入场"},
        )

    # 校验重复入场
    existing = (
        db.query(ParkingRecord)
        .filter(
            ParkingRecord.plate_number == plate_number,
            ParkingRecord.status.in_(["parking", "paid"]),
        )
        .order_by(ParkingRecord.entry_time.desc())
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail={"message": f"该车辆已在场内（{existing.status}），不可重复入场"},
        )

    now = datetime.now()
    record = ParkingRecord(
        plate_number=plate_number,
        plate_image="",
        entry_time=now,
        status="parking",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return EntryResponse(
        id=record.id,
        plate_number=record.plate_number,
        entry_time=record.entry_time,
        status=record.status,
    )
