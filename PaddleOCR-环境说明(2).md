# step_c: PaddleOCR 车牌识别

## 概述

使用 PaddleOCR 深度学习引擎直接识别车牌，无需字符分割。基于 DBNet（文字检测）+ CRNN（文字识别），中文识别精度远高于传统引擎。

**最终识别结果**：豫B·60P70，置信度 **0.997**

---

## 环境安装

### 1. 安装的包与库

| 包名 | 版本 | 大小 | 说明 |
|------|------|------|------|
| `paddlepaddle` | **3.2.2**（降级） | 101.7 MB | PaddlePaddle 深度学习框架 |
| `paddleocr` | 3.7.0 | 146 KB | PaddleOCR 文字识别 API |
| `paddlex` | 3.7.1 | 2.2 MB | PaddleX 基础模块（OCR核心） |

> **注意**：`paddlepaddle` 最初安装了 3.3.1，后因 oneDNN 兼容性 bug 降级到 3.2.2。

### 2. 安装命令

```powershell
# 安装到项目虚拟环境
venv\Scripts\pip.exe install paddlepaddle paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple

# 降级 paddlepaddle（解决 oneDNN bug）
venv\Scripts\pip.exe install paddlepaddle==3.2.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. pip 包的两个存储位置

| 位置 | 路径 | 说明 |
|------|------|------|
| 下载缓存 | `D:\Users\mayib\AppData\Local\pip\cache` | `.whl` 文件的缓存，下次安装同版本不再下载 |
| 实际安装 | `venv\Lib\site-packages\` | Python import 时搜索的位置，`paddle/` 目录 373.6 MB |

---

## 自动下载的模型

首次运行 PaddleOCR 时，PaddleX 会自动从官网下载模型文件到 `C:\Users\mayib\.paddlex\official_models\`。

| 模型 | 大小 | 用途 |
|------|------|------|
| `PP-LCNet_x1_0_doc_ori` | 6.87 MB | 文档方向分类器 |
| `UVDoc` | 32.3 MB | 文档矫正（去扭曲） |
| `PP-LCNet_x1_0_textline_ori` | 6.87 MB | 文字方向分类 |
| `PP-OCRv6_medium_det` | 62.3 MB | 文字检测网络（DBNet） |
| `PP-OCRv6_medium_rec` | 76.9 MB | 文字识别网络（CRNN） |
| **合计** | **~187 MB** | |

模型下载一次后会缓存，后续运行直接加载缓存。

---

## 遇到的问题与解决方案

### 问题1：PaddlePaddle 3.3.1 + oneDNN 兼容性 bug

**错误信息**：

```
NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute
not support [pir::ArrayAttribute<pir::DoubleAttribute>]
(at ..\paddle\fluid\framework\new_executor\instruction\onednn\onednn_instruction.cc:118)
```

**原因**：PaddlePaddle 3.3.1 的 PIR（Paddle Intermediate Representation）与 oneDNN 算子库存在兼容性问题，在 Windows 上执行文字检测模型时会崩溃。

**解决**：降级到 `paddlepaddle==3.2.2`，同时设置环境变量禁用 oneDNN：

```python
os.environ['FLAGS_use_onednn'] = '0'
```

---

### 问题2：PaddleOCR 3.7.0 API 变化

**错误信息**：

```
ValueError: Unknown argument: show_log
TypeError: PaddleOCR.predict() got an unexpected keyword argument 'cls'
DeprecationWarning: Please use `predict` instead.
```

**原因**：PaddleOCR 3.x 进行了大幅 API 重构：

| 旧 API（≤2.x） | 新 API（3.x） |
|---------------|--------------|
| `ocr = PaddleOCR(use_angle_cls=True)` | `ocr = PaddleOCR(use_textline_orientation=True)` |
| `result = ocr.ocr(img, cls=True)` | `result = ocr.predict(img)` |
| 返回 `list[list[bbox, (text, score)]]` | 返回 `list[OCRResult]` |

**解决**：改用 `predict()` 方法，通过 `OCRResult` 对象的 `rec_texts` 和 `rec_scores` 字段获取结果：

```python
result = ocr.predict(image)
for item in result:
    text = item['rec_texts'][0]      # 识别文本
    score = item['rec_scores'][0]    # 置信度
```

---

### 问题3：rec_texts 读取为空的调试过程

脚本最初能运行但识别结果为空，原因是 `predict()` 返回的是 `OCRResult` 对象（类字典），而不是旧的 `list[list]` 格式。代码中按旧格式解析导致读取不到。

**解决**：写了一个临时调试脚本 `debug_predict.py`，打印出完整的返回结构，确认了 `OCRResult` 的字段名：

```python
# OCRResult 关键字段
{
    'rec_texts': ['豫B·60P70'],        # 识别文本列表
    'rec_scores': [0.997217059135437],  # 置信度列表
    'dt_polys': [...],                  # 检测框多边形
    'rec_polys': [...],                 # 识别框多边形
    'textline_orientation_angles': [0], # 文字方向角度
}
```

---

## 三种识别方案对比

| 方案 | 识别结果 | 置信度 | 需要分割 | 汉字识别 | 依赖大小 |
|------|----------|--------|----------|----------|----------|
| 模板匹配 (step_a) | 豫B60P70 | 0.811 | **是** | 依赖模板字体 | ~500KB |
| Tesseract (step_b) | 8B60P70 | 0.43 | 否 | **失败** | ~50MB |
| **PaddleOCR (step_c)** | **豫B·60P70** | **0.997** | **否** | **完美** | ~373MB |

---

## 使用方式

```powershell
venv\Scripts\python.exe step_c_paddle\step_c.py
```

前提：已运行 step_6（倾斜校正）和 step_7（二值化），生成输入文件。

---

## 文件清单

```
step_c_paddle/
  ├── step_c.py           ← 主脚本
  ├── step_c_output.png   ← 识别结果可视化
  └── 说明.md             ← 本文档
```
