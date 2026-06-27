"""车牌识别系统 — 单文件版

用法:
    命令行:  python main.py <图片路径> [图片路径 ...]
    代码导入: from main import PlateRecognizer

依赖:
    pip install paddlepaddle==3.2.2 paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
"""
import sys
import time
import os
import cv2
import numpy as np
from paddleocr import PaddleOCR

# ============================================================
#  PaddleOCR 初始化
# ============================================================
os.environ['FLAGS_use_onednn'] = '0'  # 禁用 oneDNN，避免兼容性 bug

_ocr = None

def _get_ocr():
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(use_textline_orientation=True)
    return _ocr


# ============================================================
#  车牌定位
# ============================================================
MAX_DIM = 1200


def _resize_if_large(image, max_dim=MAX_DIM):
    h, w = image.shape[:2]
    if max(h, w) <= max_dim:
        return image, 1.0
    scale = max_dim / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h)), scale


def _edge_locate(gray, img_area):
    """Sobel边缘检测 + 形态学"""
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    sobel_x = cv2.Sobel(blurred, cv2.CV_16S, 1, 0, ksize=3)
    sobel_x = cv2.convertScaleAbs(sobel_x)
    _, binary = cv2.threshold(sobel_x, 0, 255, cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area, ratio = cw * ch, (cw / ch if ch > 0 else 0)
        if area < 1000 or area > img_area * 0.6: continue
        if not (1.8 < ratio < 6.0): continue
        if ch < 12: continue
        candidates.append((x, y, cw, ch, area))
    return candidates


def _blue_locate(image_bgr):
    """蓝色HSV颜色分割"""
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([135, 255, 255]))

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    h, w = image_bgr.shape[:2]
    img_area = h * w
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area, ratio = cw * ch, (cw / ch if ch > 0 else 0)
        if area < 500 or area > img_area * 0.5: continue
        if not (1.8 < ratio < 6.0): continue
        if ch < 10: continue
        candidates.append((x, y, cw, ch, area))
    return candidates


def _locate_plate(image):
    """定位车牌，返回(灰度ROI, 原图坐标)或None"""
    h, w = image.shape[:2]
    if h < 100 or w < 100:
        return None

    img_resized, scale = _resize_if_large(image)
    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    rh, rw = img_resized.shape[:2]

    candidates = _blue_locate(img_resized)
    if not candidates:
        candidates = _edge_locate(gray, rh * rw)
    if not candidates:
        return None

    candidates.sort(key=lambda t: t[4], reverse=True)
    x, y, cw, ch, _ = candidates[0]

    pad_w, pad_h = int(cw * 0.1), int(ch * 0.2)
    x1, y1 = max(0, x - pad_w), max(0, y - pad_h)
    x2, y2 = min(rw, x + cw + pad_w), min(rh, y + ch + pad_h)

    roi = gray[y1:y2, x1:x2]

    if scale != 1.0:
        x1_o, y1_o = int(x1 / scale), int(y1 / scale)
        x2_o, y2_o = int(x2 / scale), int(y2 / scale)
        roi = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)[y1_o:y2_o, x1_o:x2_o]
        return roi, (x1_o, y1_o, x2_o, y2_o)
    return roi, (x1, y1, x2, y2)


# ============================================================
#  车牌预处理
# ============================================================
def _preprocess_plate(plate_gray):
    """CLAHE增强 + OTSU二值化 + 去噪 + 裁剪黑边"""
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(plate_gray)

    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    denoised = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    coords = cv2.findNonZero(denoised)
    if coords is not None:
        x, y, cw, ch = cv2.boundingRect(coords)
        denoised = denoised[y:y + ch, x:x + cw]
    return denoised


# ============================================================
#  OCR 识别
# ============================================================
def _ocr_recognize(plate_img):
    """PaddleOCR 识别，返回 {text, confidence, success}"""
    ocr = _get_ocr()
    if len(plate_img.shape) == 2:
        plate_img = cv2.cvtColor(plate_img, cv2.COLOR_GRAY2BGR)

    result = ocr.predict(plate_img)
    texts, scores = [], []
    for item in result:
        for t, s in zip(item.get('rec_texts', []), item.get('rec_scores', [])):
            texts.append(t)
            scores.append(s)

    if not texts:
        return {'text': '', 'confidence': 0.0, 'success': False}
    return {
        'text': ''.join(texts),
        'confidence': round(float(np.mean(scores)), 4),
        'success': True
    }


# ============================================================
#  PlateRecognizer 封装类
# ============================================================
class PlateRecognizer:
    """车牌识别器

    用法:
        r = PlateRecognizer()
        result = r.recognize("car.jpg")
        print(result['text'])        # 豫B·60P70
        print(result['confidence'])  # 0.9981
    """

    def __init__(self, verbose: bool = True):
        self._verbose = verbose
        self._locate_time = 0.0
        self._ocr_time = 0.0

    @property
    def locate_time(self) -> float:
        return self._locate_time

    @property
    def ocr_time(self) -> float:
        return self._ocr_time

    @property
    def total_time(self) -> float:
        return self._locate_time + self._ocr_time

    def recognize(self, image) -> dict:
        """识别车牌。image 可以是路径(str)或BGR numpy数组。"""
        if isinstance(image, str):
            if self._verbose:
                print(f"[读取] {image}")
            img = cv2.imread(image)
            if img is None:
                return {'text': '', 'confidence': 0.0, 'success': False,
                        'error': f'无法读取: {image}'}
        else:
            img = image

        # 定位
        t0 = time.time()
        located = _locate_plate(img)
        self._locate_time = time.time() - t0
        if located is None:
            return {'text': '', 'confidence': 0.0, 'success': False}
        plate_roi, _ = located
        if self._verbose:
            print(f"  -> 定位: {plate_roi.shape[1]}x{plate_roi.shape[0]} ({self._locate_time:.2f}s)")

        # 预处理
        processed = _preprocess_plate(plate_roi)

        # OCR
        t0 = time.time()
        result = _ocr_recognize(processed)
        self._ocr_time = time.time() - t0
        if self._verbose and result['success']:
            print(f"  -> 识别: {result['text']}  置信度: {result['confidence']}  ({self._ocr_time:.2f}s)")

        return result


# ============================================================
#  命令行入口
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python main.py <图片路径> [图片路径 ...]")
        sys.exit(1)

    r = PlateRecognizer(verbose=True)
    for path in sys.argv[1:]:
        result = r.recognize(path)
        if result['success']:
            print(f"结果: {result['text']}  (置信度: {result['confidence']})")
        else:
            print(f"识别失败: {result.get('error', '未检测到车牌')}")
        print()
