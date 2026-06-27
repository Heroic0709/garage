"""
车牌识别服务
封装现有的 main.py 中的 PlateRecognizer，提供：
- 接收 FastAPI UploadFile
- 保存图片到 uploads/
- 调用识别引擎
- 返回结构化结果
"""

import os
import sys
import uuid
from typing import Dict

from fastapi import UploadFile

from backend.config import UPLOAD_DIR

# ============================================================
# 将项目根目录加入 sys.path，以便导入 main.py 中的 PlateRecognizer
# ============================================================
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# 延迟初始化，首次调用时才加载（PaddleOCR 加载较慢）
_recognizer = None


def _get_recognizer():
    """延迟加载识别器（单例），避免启动时就加载 PaddleOCR"""
    global _recognizer
    if _recognizer is None:
        # main.py 在导入时会自动设置 FLAGS_use_onednn = '0'
        from main import PlateRecognizer
        _recognizer = PlateRecognizer(verbose=False)
    return _recognizer


async def recognize_and_save(image_file: UploadFile) -> Dict:
    """
    接收上传的车牌图片，保存并识别

    参数:
        image_file: FastAPI UploadFile 对象

    返回:
        {
            'plate_number': '豫B·60P70',   # 识别成功时有值
            'confidence': 0.998,           # 置信度
            'image_path': 'uploads/xxx.jpg',  # 保存的图片相对路径
            'success': True,               # 是否识别成功
            'error': ''                    # 失败原因
        }
    """
    # 生成唯一文件名
    ext = os.path.splitext(image_file.filename or "image.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 保存文件
    content = await image_file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # 调用识别引擎
    try:
        recognizer = _get_recognizer()
        result = recognizer.recognize(filepath)

        if result.get("success"):
            return {
                "plate_number": result.get("text", ""),
                "confidence": round(result.get("confidence", 0.0), 4),
                "image_path": os.path.join("uploads", filename),
                "success": True,
                "error": "",
            }
        else:
            return {
                "plate_number": "",
                "confidence": 0.0,
                "image_path": os.path.join("uploads", filename),
                "success": False,
                "error": result.get("error", "车牌识别失败，请重试"),
            }
    except Exception as e:
        return {
            "plate_number": "",
            "confidence": 0.0,
            "image_path": os.path.join("uploads", filename),
            "success": False,
            "error": f"识别异常: {str(e)}",
        }
