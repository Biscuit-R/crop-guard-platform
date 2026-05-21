"""
模型版本管理工具
支持语义化版本命名（v1.0.0）+ 时间戳
"""
import os
import json
from datetime import datetime
from typing import Optional


class VersionManager:
    """模型版本管理器"""

    def __init__(self, versions_file: str = "versions.json"):
        """
        初始化版本管理器

        Args:
            versions_file: 版本记录文件路径
        """
        self.versions_file = versions_file
        self.versions = self._load_versions()

    def _load_versions(self) -> dict:
        """加载版本记录"""
        if os.path.exists(self.versions_file):
            try:
                with open(self.versions_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"[版本管理] 警告: {self.versions_file} 格式损坏，将重新创建")
        return {
            "current_version": "v0.0.0",
            "versions": [],
        }

    def _save_versions(self):
        """保存版本记录"""
        with open(self.versions_file, "w", encoding="utf-8") as f:
            json.dump(self.versions, f, ensure_ascii=False, indent=2)

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self.versions["current_version"]

    def get_next_version(self, bump_type: str = "patch") -> str:
        """
        获取下一个版本号

        Args:
            bump_type: 版本升级类型 (major/minor/patch)
                - major: 主版本号 (v1.0.0 -> v2.0.0)
                - minor: 次版本号 (v1.0.0 -> v1.1.0)
                - patch: 补丁版本号 (v1.0.0 -> v1.0.1)

        Returns:
            下一个版本号
        """
        current = self.get_current_version()
        # 移除 'v' 前缀
        version = current.removeprefix("v")
        major, minor, patch = map(int, version.split("."))

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return f"v{major}.{minor}.{patch}"

    def create_version(
        self,
        version: Optional[str] = None,
        bump_type: str = "patch",
        model_path: str = None,
        metrics: dict = None,
        training_config: dict = None,
        description: str = None,
    ) -> dict:
        """
        创建新版本

        Args:
            version: 指定版本号（可选，不指定则自动递增）
            bump_type: 版本升级类型
            model_path: 模型文件路径
            metrics: 训练指标
            training_config: 训练配置
            description: 版本描述

        Returns:
            版本信息字典
        """
        if version is None:
            version = self.get_next_version(bump_type)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        version_info = {
            "version": version,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "model_path": model_path,
            "metrics": metrics or {},
            "training_config": training_config or {},
            "description": description or "",
            "status": "active",
        }

        # 更新版本记录
        self.versions["current_version"] = version
        self.versions["versions"].append(version_info)
        self._save_versions()

        print(f"[版本管理] 创建新版本: {version}")
        return version_info

    def get_version(self, version: str) -> Optional[dict]:
        """
        获取指定版本信息

        Args:
            version: 版本号

        Returns:
            版本信息字典
        """
        for v in self.versions["versions"]:
            if v["version"] == version:
                return v
        return None

    def list_versions(self, limit: int = 10) -> list:
        """
        列出最近的版本

        Args:
            limit: 返回数量限制

        Returns:
            版本列表
        """
        return self.versions["versions"][-limit:]

    def get_model_name(self, version: str, base_name: str = "crop_guard") -> str:
        """
        生成带版本号的模型名称

        Args:
            version: 版本号
            base_name: 基础名称

        Returns:
            模型名称，如 crop_guard_v1.0.0
        """
        return f"{base_name}_{version}"

    def get_minio_path(self, version: str, base_name: str = "crop_guard") -> str:
        """
        生成 MinIO 存储路径

        Args:
            version: 版本号
            base_name: 基础名称

        Returns:
            MinIO 路径，如 models/crop_guard/v1.0.0/20260520_170000
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"models/{base_name}/{version}/{timestamp}"


# 全局实例
_version_manager = None


def get_version_manager(versions_file: str = None) -> VersionManager:
    """获取版本管理器实例"""
    global _version_manager
    if _version_manager is None:
        if versions_file is None:
            # 默认在 training 目录下
            script_dir = os.path.dirname(os.path.abspath(__file__))
            versions_file = os.path.join(script_dir, "versions.json")
        _version_manager = VersionManager(versions_file)
    return _version_manager
