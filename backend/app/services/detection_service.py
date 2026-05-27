import logging
import os
import glob
import json
import time
import uuid
import threading
from datetime import datetime, timezone
from ultralytics import YOLO
import cv2
import numpy as np
from app.config import settings, MODEL_REGISTRY, CHINESE_CLASS_NAMES
from app.models.schemas import DetectionBox, DetectionResult, VideoDetectionResult, ModelInfo, VersionHistoryItem
from app.utils.file_utils import get_file_url

logger = logging.getLogger(__name__)


# ==================== 美化检测框绘制 ====================

# 类别调色板（20色循环，HSV 均匀分布转 BGR）
_PALETTE = [
    (72, 209, 173),   # 暖绿
    (50, 127, 233),   # 天蓝
    (46, 199, 106),   # 草绿
    (138, 87, 232),   # 紫罗兰
    (34, 178, 229),   # 青蓝
    (57, 199, 186),   # 青绿
    (232, 110, 48),   # 暖橙
    (131, 96, 232),   # 蓝紫
    (217, 83, 79),    # 珊瑚红
    (50, 142, 232),   # 宝蓝
    (92, 184, 77),    # 浅绿
    (227, 156, 37),   # 琥珀黄
    (66, 133, 244),   # Google蓝
    (120, 178, 52),   # 黄绿
    (219, 68, 55),    # Google红
    (244, 180, 0),    # 金黄
    (171, 71, 188),   # 梅紫
    (0, 172, 193),    # 深青
    (255, 112, 67),   # 深橙
    (124, 179, 66),   # 橄榄绿
]


def _get_color(class_id: int) -> tuple:
    """根据类别 ID 返回一个 BGR 颜色"""
    return _PALETTE[class_id % len(_PALETTE)]


def _rounded_rect(img, pt1, pt2, color, radius=12, thickness=1):
    """绘制圆角矩形边框"""
    x1, y1 = pt1
    x2, y2 = pt2
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    if r < 1:
        cv2.rectangle(img, pt1, pt2, color, thickness)
        return

    # 四条边（不含圆角弧）
    cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
    cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)

    # 四段圆弧
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)


def _fill_rounded_rect(img, pt1, pt2, color, radius=12, alpha=0.15):
    """绘制半透明填充圆角矩形"""
    x1, y1 = pt1
    x2, y2 = pt2
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    if r < 1:
        overlay = img.copy()
        cv2.rectangle(overlay, pt1, pt2, color, -1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        return

    overlay = img.copy()

    # 填充主体区域
    cv2.rectangle(overlay, (x1 + r, y1), (x2 - r, y2), color, -1)
    cv2.rectangle(overlay, (x1, y1 + r), (x2, y2 - r), color, -1)

    # 四个圆角填充
    cv2.ellipse(overlay, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, -1)
    cv2.ellipse(overlay, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, -1)
    cv2.ellipse(overlay, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, -1)
    cv2.ellipse(overlay, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, -1)

    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def _draw_label(img, text, x, y, color, font_scale=0.45):
    """绘制带圆角背景的标签（含阴影）"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 1
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    label_w = tw + 14
    label_h = th + 10
    lx1 = x
    ly1 = y - label_h
    lx2 = x + label_w
    ly2 = y

    # 阴影层
    shadow = img.copy()
    cv2.rectangle(shadow, (lx1 + 2, ly1 + 2), (lx2 + 2, ly2 + 2), (0, 0, 0), -1)
    cv2.addWeighted(shadow, 0.15, img, 0.85, 0, img)

    # 背景填充（圆角矩形）
    _fill_rounded_rect(img, (lx1, ly1), (lx2, ly2), color, radius=6, alpha=0.92)

    # 文字（白色，抗锯齿）
    text_x = lx1 + 7
    text_y = ly2 - baseline - 4
    cv2.putText(img, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)


def _draw_confidence_bar(img, x1, y1, x2, y2, color, confidence, bar_h=4):
    """在检测框底部绘制置信度进度条"""
    bar_w = int((x2 - x1) * confidence)
    if bar_w < 1:
        return
    # 半透明黑色背景
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y2 - bar_h), (x2, y2), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
    # 置信度条（类色填充）
    cv2.rectangle(img, (x1, y2 - bar_h), (x1 + bar_w, y2), color, -1)


def draw_detections(image: np.ndarray, boxes: list, class_names: dict, cn_names: dict = None) -> np.ndarray:
    """
    在图片上绘制美化的检测框。

    Args:
        image: BGR 格式图片 (numpy array)
        boxes: ultralytics Results.boxes 列表
        class_names: {id: name} 字典
        cn_names: {en_name: cn_name} 中文学名字典

    Returns:
        绘制后的图片副本
    """
    img = image.copy()
    h, w = img.shape[:2]
    # 根据图片大小自适应线宽和字号
    line_w = max(2, int(min(h, w) / 300))
    font_scale = max(0.35, min(0.6, min(h, w) / 1200))

    for box in boxes:
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        confidence = float(box.conf[0])
        class_id = int(box.cls[0])
        en_name = class_names.get(class_id, f"class_{class_id}")
        display_name = cn_names.get(en_name, en_name) if cn_names else en_name
        color = _get_color(class_id)

        # 1. 半透明填充
        _fill_rounded_rect(img, (x1, y1), (x2, y2), color, radius=10, alpha=0.06)

        # 2. 圆角边框
        _rounded_rect(img, (x1, y1), (x2, y2), color, radius=10, thickness=line_w)

        # 3. 四角加粗装饰线
        corner_len = max(14, int(min(x2 - x1, y2 - y1) * 0.18))
        thick = line_w + 2
        # 左上
        cv2.line(img, (x1, y1), (x1 + corner_len, y1), color, thick, cv2.LINE_AA)
        cv2.line(img, (x1, y1), (x1, y1 + corner_len), color, thick, cv2.LINE_AA)
        # 右上
        cv2.line(img, (x2, y1), (x2 - corner_len, y1), color, thick, cv2.LINE_AA)
        cv2.line(img, (x2, y1), (x2, y1 + corner_len), color, thick, cv2.LINE_AA)
        # 左下
        cv2.line(img, (x1, y2), (x1 + corner_len, y2), color, thick, cv2.LINE_AA)
        cv2.line(img, (x1, y2), (x1, y2 - corner_len), color, thick, cv2.LINE_AA)
        # 右下
        cv2.line(img, (x2, y2), (x2 - corner_len, y2), color, thick, cv2.LINE_AA)
        cv2.line(img, (x2, y2), (x2, y2 - corner_len), color, thick, cv2.LINE_AA)

        # 4. 底部置信度进度条
        _draw_confidence_bar(img, x1, y1, x2, y2, color, confidence)

        # 5. 标签（含阴影）— 使用英文名避免 OpenCV 中文渲染乱码
        label = f"{en_name} {confidence:.0%}"
        label_y = y1 - 6
        if label_y < 30:
            label_y = y2 + 6
        _draw_label(img, label, x1, label_y, color, font_scale=font_scale)

    return img


def draw_detections_from_dicts(image: np.ndarray, detections: list) -> np.ndarray:
    """
    从字典列表绘制检测框（用于视频非检测帧复用）。

    Args:
        image: BGR 格式图片
        detections: [{"x1","y1","x2","y2","confidence","class_id","en_name"}, ...]
    """
    if not detections:
        return image

    img = image.copy()
    h, w = img.shape[:2]
    line_w = max(2, int(min(h, w) / 300))
    font_scale = max(0.35, min(0.6, min(h, w) / 1200))

    for det in detections:
        x1, y1, x2, y2 = int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"])
        confidence = det["confidence"]
        class_id = det["class_id"]
        en_name = det["en_name"]
        color = _get_color(class_id)

        _fill_rounded_rect(img, (x1, y1), (x2, y2), color, radius=10, alpha=0.06)
        _rounded_rect(img, (x1, y1), (x2, y2), color, radius=10, thickness=line_w)

        corner_len = max(14, int(min(x2 - x1, y2 - y1) * 0.18))
        thick = line_w + 2
        cv2.line(img, (x1, y1), (x1 + corner_len, y1), color, thick, cv2.LINE_AA)
        cv2.line(img, (x1, y1), (x1, y1 + corner_len), color, thick, cv2.LINE_AA)
        cv2.line(img, (x2, y1), (x2 - corner_len, y1), color, thick, cv2.LINE_AA)
        cv2.line(img, (x2, y1), (x2, y1 + corner_len), color, thick, cv2.LINE_AA)
        cv2.line(img, (x1, y2), (x1 + corner_len, y2), color, thick, cv2.LINE_AA)
        cv2.line(img, (x1, y2), (x1, y2 - corner_len), color, thick, cv2.LINE_AA)
        cv2.line(img, (x2, y2), (x2 - corner_len, y2), color, thick, cv2.LINE_AA)
        cv2.line(img, (x2, y2), (x2, y2 - corner_len), color, thick, cv2.LINE_AA)

        _draw_confidence_bar(img, x1, y1, x2, y2, color, confidence)

        label = f"{en_name} {confidence:.0%}"
        label_y = y1 - 6
        if label_y < 30:
            label_y = y2 + 6
        _draw_label(img, label, x1, label_y, color, font_scale=font_scale)

    return img


# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DetectionService:
    def __init__(self):
        self.model = None
        self.class_names = {}
        self.current_model_path = None
        self.current_model_version = None
        self.model_mtime = 0.0
        self._lock = threading.Lock()
        self._discover_and_load()

    def _discover_latest_model(self) -> str:
        """
        自动发现最新模型，优先级：
        1. best.pt（训练脚本部署的当前模型）
        2. 最新的 best_vX.X.X.pt（版本化模型）
        3. settings.YOLO_MODEL_PATH（配置回退）
        """
        models_dir = settings.MODEL_DIR

        best = os.path.join(models_dir, "best.pt")
        if os.path.exists(best):
            return best

        versioned = glob.glob(os.path.join(models_dir, "best_v*.pt"))
        if versioned:
            return max(versioned, key=os.path.getmtime)

        # model_*.pt 命名
        model_files = glob.glob(os.path.join(models_dir, "model_*.pt"))
        if model_files:
            return max(model_files, key=os.path.getmtime)

        return settings.YOLO_MODEL_PATH

    def _extract_version(self, path: str) -> str:
        name = os.path.basename(path)
        if name.startswith("model_"):
            return name.replace("model_", "").replace(".pt", "") + "类"
        return os.path.splitext(name)[0]

    def _discover_and_load(self):
        model_path = self._discover_latest_model()
        self._load_model(model_path)

    def _load_model(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        self.model = YOLO(model_path)
        self.class_names = self.model.names
        self.current_model_path = model_path
        self.model_mtime = os.path.getmtime(model_path)
        self.current_model_version = self._extract_version(model_path)

        logger.info("[模型加载] 路径: %s", model_path)
        logger.info("[模型加载] 版本: %s", self.current_model_version)
        logger.info("[模型加载] 类别数: %d", len(self.class_names))

    def check_and_reload(self) -> bool:
        """检查模型文件是否更新，如更新则重载。返回是否发生重载。"""
        model_path = self._discover_latest_model()

        # 模型文件变了（换了一个文件）
        if os.path.abspath(model_path) != os.path.abspath(self.current_model_path):
            logger.info("[模型更新] 发现新模型文件: %s", model_path)
            with self._lock:
                self._load_model(model_path)
            return True

        # 同一文件但内容更新了（mtime 变化）
        current_mtime = os.path.getmtime(model_path)
        if current_mtime > self.model_mtime:
            logger.info("[模型更新] 检测到模型文件更新: %s", model_path)
            with self._lock:
                self._load_model(model_path)
            return True

        return False

    def reload(self) -> dict:
        """手动强制重载，返回状态信息"""
        with self._lock:
            self._discover_and_load()
        return self.get_status()

    def get_status(self) -> dict:
        """返回当前模型状态"""
        return {
            "model_path": self.current_model_path,
            "model_version": self.current_model_version,
            "model_mtime": datetime.fromtimestamp(self.model_mtime, tz=timezone.utc).isoformat() if self.model_mtime else None,
            "class_count": len(self.class_names),
            "is_loaded": self.model is not None,
        }

    def list_models(self) -> list:
        """列出 models 目录下所有可用模型"""
        models_dir = settings.MODEL_DIR
        if not os.path.isdir(models_dir):
            return []

        models = []
        current_abs = os.path.abspath(self.current_model_path) if self.current_model_path else None

        for f in os.listdir(models_dir):
            if f.endswith(".pt"):
                full_path = os.path.join(models_dir, f)
                version = self._extract_version(full_path)
                stat = os.stat(full_path)
                reg = MODEL_REGISTRY.get(f, {})
                models.append(ModelInfo(
                    filename=f,
                    version=version,
                    size_mb=round(stat.st_size / (1024 * 1024), 2),
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    is_current=os.path.abspath(full_path) == current_abs,
                    display_name=reg.get("display_name", version),
                    description=reg.get("description", ""),
                ))

        # 按修改时间降序
        models.sort(key=lambda m: m.modified_at, reverse=True)
        return models

    def switch_model(self, version: str) -> dict:
        """
        切换到指定版本的模型

        Args:
            version: 版本号（如 v1.0.0）或文件名（如 best.pt、yolo11n.pt）
        """
        models_dir = settings.MODEL_DIR

        # 直接文件名匹配
        if version.endswith(".pt"):
            target = os.path.join(models_dir, version)
        else:
            # 版本号匹配：best_v1.0.0.pt
            target = os.path.join(models_dir, f"best_{version}.pt")

        if not os.path.exists(target):
            # 尝试模糊匹配
            candidates = glob.glob(os.path.join(models_dir, f"*{version}*.pt"))
            if candidates:
                target = candidates[0]
            else:
                raise FileNotFoundError(f"未找到版本 {version} 对应的模型文件")

        with self._lock:
            self._load_model(target)
        logger.info("[模型切换] 已切换到: %s (版本: %s)", target, self.current_model_version)
        return self.get_status()

    def get_version_history(self) -> list:
        """读取训练版本历史（从 training/versions.json）"""
        versions_file = os.path.join(PROJECT_DIR, "training", "versions.json")
        if not os.path.exists(versions_file):
            return []

        try:
            with open(versions_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            history = []
            for v in data.get("versions", []):
                history.append(VersionHistoryItem(
                    version=v.get("version", ""),
                    created_at=v.get("created_at", ""),
                    description=v.get("description", ""),
                    metrics=v.get("metrics", {}),
                ))
            history.reverse()  # 最新的在前
            return history
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("[版本历史] 读取失败: %s", e)
            return []

    def detect_single_image(self, image_path: str, model_name: str = "pest-v1", conf: float = None) -> DetectionResult:
        # 检测前自动检查模型更新
        self.check_and_reload()

        with self._lock:
            start_time = time.time()
            detection_id = str(uuid.uuid4())

            results = self.model.predict(
                source=image_path,
                conf=conf if conf is not None else settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD,
                save=False
            )

            boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    en_name = self.class_names.get(class_id, f"class_{class_id}")
                    cn_name = CHINESE_CLASS_NAMES.get(en_name, en_name)

                    boxes.append(DetectionBox(
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        confidence=confidence,
                        class_id=class_id,
                        class_name=en_name,
                        chinese_name=cn_name,
                    ))

            result_filename = f"result_{uuid.uuid4().hex}.jpg"
            result_path = os.path.join(settings.RESULT_DIR, result_filename)

            annotated_image = draw_detections(results[0].orig_img, results[0].boxes, self.class_names, CHINESE_CLASS_NAMES)
            cv2.imwrite(result_path, annotated_image)

            detection_time = time.time() - start_time
            image_filename = os.path.basename(image_path)

            return DetectionResult(
                detection_id=detection_id,
                image_url=get_file_url(image_filename, settings.UPLOAD_DIR),
                result_image_url=get_file_url(result_filename, settings.RESULT_DIR),
                boxes=boxes,
                total_objects=len(boxes),
                detection_time=round(detection_time, 3),
                model_name=model_name,
                created_at=datetime.now(timezone.utc)
            )

    def detect_video(self, video_path: str, model_name: str = "pest-v1",
                     conf: float = None, frame_interval: int = 5) -> VideoDetectionResult:
        self.check_and_reload()

        with self._lock:
            start_time = time.time()
            detection_id = str(uuid.uuid4())
            conf_threshold = conf if conf is not None else settings.CONFIDENCE_THRESHOLD

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0

            # 准备输出视频
            result_filename = f"result_{uuid.uuid4().hex}.mp4"
            result_path = os.path.join(settings.RESULT_VIDEO_DIR, result_filename)
            fourcc = cv2.VideoWriter_fourcc(*"avc1")
            writer = cv2.VideoWriter(result_path, fourcc, fps, (width, height))

            try:
                # === 跨帧去重追踪 ===
                # tracked_objects: [{class_id, cn_name, x1,y1,x2,y2, confidence, last_seen}]
                tracked_objects = []
                TRACK_IOU_THRESH = 0.3
                TRACK_MAX_GAP = int(fps * 2)  # 超过 2 秒未见则视为消失

                def _box_iou(a, b):
                    ix1 = max(a[0], b[0]); iy1 = max(a[1], b[1])
                    ix2 = min(a[2], b[2]); iy2 = min(a[3], b[3])
                    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                    area_a = (a[2] - a[0]) * (a[3] - a[1])
                    area_b = (b[2] - b[0]) * (b[3] - b[1])
                    union = area_a + area_b - inter
                    return inter / union if union > 0 else 0

                key_frames = []
                processed_frames = 0
                frame_idx = 0
                # 暂存上一次检测结果，用于非检测帧复用绘制
                last_detections = []
                PERSIST_FRAMES = frame_interval * 3  # 检测框留存帧数（约 3 个检测间隔）

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_idx % frame_interval == 0:
                        results = self.model.predict(
                            source=frame,
                            conf=conf_threshold,
                            iou=settings.IOU_THRESHOLD,
                            save=False,
                            verbose=False,
                        )

                        annotated = draw_detections(results[0].orig_img, results[0].boxes, self.class_names, CHINESE_CLASS_NAMES)
                        writer.write(annotated)

                        # 缓存当前帧检测结果供后续帧复用
                        last_detections = []
                        for box in results[0].boxes:
                            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                            confidence = float(box.conf[0])
                            class_id = int(box.cls[0])
                            en_name = self.class_names.get(class_id, f"class_{class_id}")
                            cn_name = CHINESE_CLASS_NAMES.get(en_name, en_name)
                            last_detections.append({
                                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                                "confidence": confidence,
                                "class_id": class_id,
                                "en_name": en_name,
                                "seen_at": frame_idx,
                            })

                        # 去重追踪
                        for det in last_detections:
                            best_iou = 0
                            best_idx = -1
                            for i, tr in enumerate(tracked_objects):
                                if tr["class_id"] != det["class_id"]:
                                    continue
                                if frame_idx - tr["last_seen"] > TRACK_MAX_GAP:
                                    continue
                                iou = _box_iou(
                                    (det["x1"], det["y1"], det["x2"], det["y2"]),
                                    (tr["x1"], tr["y1"], tr["x2"], tr["y2"]),
                                )
                                if iou > best_iou:
                                    best_iou = iou
                                    best_idx = i

                            if best_iou >= TRACK_IOU_THRESH:
                                tr = tracked_objects[best_idx]
                                tr["x1"], tr["y1"], tr["x2"], tr["y2"] = det["x1"], det["y1"], det["x2"], det["y2"]
                                tr["confidence"] = max(tr["confidence"], det["confidence"])
                                tr["last_seen"] = frame_idx
                            else:
                                tracked_objects.append({
                                    "class_id": det["class_id"],
                                    "cn_name": CHINESE_CLASS_NAMES.get(det["en_name"], det["en_name"]),
                                    "x1": det["x1"], "y1": det["y1"], "x2": det["x2"], "y2": det["y2"],
                                    "confidence": det["confidence"],
                                    "last_seen": frame_idx,
                                })

                        # 保存关键帧（有检测目标的帧）
                        if len(results[0].boxes) > 0 and len(key_frames) < 10:
                            kf_filename = f"kf_{uuid.uuid4().hex}.jpg"
                            kf_path = os.path.join(settings.RESULT_VIDEO_DIR, kf_filename)
                            cv2.imwrite(kf_path, annotated)
                            key_frames.append(get_file_url(kf_filename, settings.RESULT_VIDEO_DIR))

                        processed_frames += 1
                    else:
                        # 非检测帧：复用上一次的检测框绘制，消除闪烁
                        recent = [d for d in last_detections if frame_idx - d["seen_at"] < PERSIST_FRAMES]
                        if recent:
                            annotated = draw_detections_from_dicts(frame, recent)
                            writer.write(annotated)
                        else:
                            writer.write(frame)

                    frame_idx += 1
            finally:
                cap.release()
                writer.release()

            # 汇总去重结果
            class_summary = {}
            for tr in tracked_objects:
                cn = tr["cn_name"]
                class_summary[cn] = class_summary.get(cn, 0) + 1

            detection_time = time.time() - start_time
            video_filename = os.path.basename(video_path)

            return VideoDetectionResult(
                detection_id=detection_id,
                video_url=get_file_url(video_filename, settings.VIDEO_DIR),
                result_video_url=get_file_url(result_filename, settings.RESULT_VIDEO_DIR),
                total_objects=len(tracked_objects),
                total_frames=total_frames,
                processed_frames=processed_frames,
                fps=round(fps, 2),
                duration=round(duration, 2),
                detection_time=round(detection_time, 3),
                model_name=model_name,
                created_at=datetime.now(timezone.utc),
                summary=class_summary,
                key_frames=key_frames,
            )


detection_service = DetectionService()
