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
from app.config import settings
from app.models.schemas import DetectionBox, DetectionResult, ModelInfo, VersionHistoryItem
from app.utils.file_utils import get_file_url

logger = logging.getLogger(__name__)

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

        return settings.YOLO_MODEL_PATH

    def _extract_version(self, path: str) -> str:
        name = os.path.basename(path)
        if name == "best.pt":
            return "latest"
        if name.startswith("best_v"):
            return name.replace("best_", "").replace(".pt", "")
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
                models.append(ModelInfo(
                    filename=f,
                    version=version,
                    size_mb=round(stat.st_size / (1024 * 1024), 2),
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    is_current=os.path.abspath(full_path) == current_abs,
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

    def detect_single_image(self, image_path: str, model_name: str = "pest-v1") -> DetectionResult:
        # 检测前自动检查模型更新
        self.check_and_reload()

        with self._lock:
            start_time = time.time()
            detection_id = str(uuid.uuid4())

            results = self.model.predict(
                source=image_path,
                conf=settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD,
                save=False
            )

            boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.class_names.get(class_id, f"class_{class_id}")

                    boxes.append(DetectionBox(
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        confidence=confidence,
                        class_id=class_id,
                        class_name=class_name
                    ))

            result_filename = f"result_{uuid.uuid4().hex}.jpg"
            result_path = os.path.join(settings.RESULT_DIR, result_filename)

            annotated_image = results[0].plot()
            cv2.imwrite(result_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

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


detection_service = DetectionService()
