"""
统一日志模块
集中管理日志配置，支持控制台和文件输出
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from app.utils.paths import Paths


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    log_dir: str = None,
    module_name: str = None,
) -> logging.Logger:
    """
    配置统一日志

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件名，None 则只输出到控制台
        log_dir: 日志目录，默认使用 Paths.logs()
        module_name: 模块名称，默认使用调用者的模块名

    Returns:
        logging.Logger: 配置好的 logger
    """
    # 获取 logger
    name = module_name or _get_caller_module()
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 设置级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler（可选）
    if log_file:
        log_dir_path = Path(log_dir) if log_dir else Paths.logs()
        log_dir_path.mkdir(parents=True, exist_ok=True)

        # 自动生成带时间戳的文件名
        if not log_file.endswith(".log"):
            log_file = f"{log_file}.log"

        file_handler = logging.FileHandler(
            log_dir_path / log_file,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def _get_caller_module() -> str:
    """获取调用者的模块名"""
    import inspect
    frame = inspect.stack()[2]
    module = inspect.getmodule(frame)
    return module.__name__ if module else __name__


def get_logger(name: str = None) -> logging.Logger:
    """
    获取 logger 的便捷方法

    Usage:
        from app.utils.logging_utils import get_logger
        logger = get_logger(__name__)
        logger.info("Hello")
    """
    if name is None:
        name = _get_caller_module()
    return logging.getLogger(name)
