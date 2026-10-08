"""YOLO 推理适配器（外部产物，平台只服务化 —— CLAUDE.md「明确不做」）。

类别名从模型的 names 表按**索引→英文名**取，再由 service 层映射中文名。
handoff 3.1：与语料的对应必须走名字，索引直接对语料会静默错 5 条。
"""

from functools import lru_cache

import cv2
import numpy as np
from ultralytics import YOLO

from app.core.config import get_settings
from app.modules.detection.service import Detection


class UltralyticsDetector:
    def __init__(self, model_path: str):
        self._model = YOLO(model_path)

    def detect(self, image: bytes) -> tuple[list[Detection], bytes]:
        img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("图片解码失败")
        results = self._model.predict(img, verbose=False)
        result = results[0]

        detections: list[Detection] = []
        boxes = result.boxes
        if boxes is not None:
            for xyxy, cls, conf in zip(boxes.xyxy.tolist(), boxes.cls.tolist(),
                                       boxes.conf.tolist()):
                detections.append(Detection(
                    class_name=self._model.names[int(cls)],
                    confidence=round(float(conf), 4),
                    bbox=[round(float(v), 1) for v in xyxy],
                ))

        plotted = result.plot()  # BGR 标注图
        ok, encoded = cv2.imencode(".jpg", plotted)
        if not ok:
            raise ValueError("标注图编码失败")
        return detections, encoded.tobytes()


@lru_cache
def get_detector() -> UltralyticsDetector:
    return UltralyticsDetector(get_settings().model_path)
