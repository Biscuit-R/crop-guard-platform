"""
路径管理模块
统一管理项目所有路径，支持从任意子模块定位项目根目录
"""
import inspect
from pathlib import Path

MARKER_FILE = ".crop_guard"


def find_project_root(start_path=None):
    """
    从当前位置向上查找项目根目录（通过查找 marker file）
    """
    if start_path is None:
        frame = inspect.stack()[1]
        start_path = Path(frame.filename).parent

    current = Path(start_path).resolve()

    for parent in [current] + list(current.parents):
        if (parent / MARKER_FILE).exists():
            return parent

    raise FileNotFoundError(
        f"Could not find {MARKER_FILE} in {current} or any parent directory"
    )


class Paths:
    """
    项目路径管理类
    所有路径统一在此定义，避免硬编码
    """

    _root = None

    @classmethod
    def root(cls):
        """获取项目根目录"""
        if cls._root is None:
            cls._root = find_project_root()
        return cls._root

    @classmethod
    def backend(cls):
        """backend 目录"""
        return cls.root() / "backend"

    @classmethod
    def app(cls):
        """app 目录"""
        return cls.backend() / "app"

    @classmethod
    def static(cls):
        """静态文件目录"""
        return cls.backend() / "static"

    @classmethod
    def uploads(cls):
        """上传文件目录"""
        return cls.static() / "uploads"

    @classmethod
    def results(cls):
        """检测结果目录"""
        return cls.static() / "results"

    @classmethod
    def videos(cls):
        """上传视频目录"""
        return cls.static() / "videos"

    @classmethod
    def result_videos(cls):
        """标注视频结果目录"""
        return cls.static() / "result_videos"

    @classmethod
    def forum_images(cls):
        """讨论区图片目录"""
        return cls.static() / "forum_images"

    @classmethod
    def models_dir(cls):
        """模型文件目录"""
        return cls.backend() / "models"

    @classmethod
    def yolo_model(cls):
        """默认 YOLO 模型路径"""
        return cls.models_dir() / "best.pt"

    @classmethod
    def logs(cls):
        """日志目录"""
        return cls.backend() / "logs"

    @classmethod
    def temp(cls):
        """临时文件目录"""
        return cls.backend() / "temp"

    @classmethod
    def frontend(cls):
        """frontend 目录"""
        return cls.root() / "frontend"

    @classmethod
    def ensure_dir(cls, path):
        """确保目录存在，不存在则创建"""
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def init_all_dirs(cls):
        """初始化所有必要的目录结构"""
        dirs = [
            cls.static(),
            cls.uploads(),
            cls.results(),
            cls.videos(),
            cls.result_videos(),
            cls.forum_images(),
            cls.models_dir(),
            cls.logs(),
            cls.temp(),
        ]
        for dir_path in dirs:
            cls.ensure_dir(dir_path)


# 便捷导出
root = Paths.root()
backend_dir = Paths.backend()
app_dir = Paths.app()
