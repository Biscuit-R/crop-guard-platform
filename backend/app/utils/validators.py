"""
数据验证子系统
可组合、可扩展的验证管道
"""
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable

logger = logging.getLogger(__name__)


class CheckLevel(Enum):
    """检查结果级别"""
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class CheckResult:
    """单个检查结果"""
    level: CheckLevel
    message: str
    check_name: str = ""
    details: Optional[Dict[str, Any]] = None


@dataclass
class CheckContext:
    """检查上下文 - 验证器的输入数据"""
    annotations_dir: Optional[Any] = None
    images_dir: Optional[Any] = None
    model_path: Optional[Any] = None
    model_dir: Optional[Any] = None
    classes: Optional[List[str]] = None
    image_extensions: List[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".bmp"]
    )
    extra: Dict[str, Any] = field(default_factory=dict)


# 验证器注册表
_validators: Dict[str, Callable] = {}


def register_validator(name: str):
    """验证器装饰器"""
    def decorator(func):
        _validators[name] = func
        func._validator_name = name
        return func
    return decorator


def get_validator(name: str):
    """获取验证器"""
    return _validators.get(name)


def list_validators():
    """列出所有验证器"""
    return list(_validators.keys())


def run_validators(context: CheckContext, validator_names: List[str] = None) -> List[CheckResult]:
    """
    运行验证器

    Args:
        context: 检查上下文
        validator_names: 指定运行的验证器，None 表示运行全部

    Returns:
        所有检查结果
    """
    results = []
    names = validator_names if validator_names is not None else list_validators()

    for name in names:
        validator = get_validator(name)
        if validator:
            try:
                check_results = validator(context)
                for r in check_results:
                    if not r.check_name:
                        r.check_name = name
                results.extend(check_results)
            except Exception as e:
                results.append(CheckResult(
                    level=CheckLevel.ERROR,
                    message=f"验证器执行失败: {str(e)}",
                    check_name=name,
                ))

    return results


def format_report(results: List[CheckResult]) -> str:
    """格式化验证报告"""
    lines = []
    for r in results:
        icon = {"pass": "✅", "info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(r.level.value, "")
        lines.append(f"{icon} [{r.level.value.upper()}] {r.check_name}: {r.message}")
        if r.details:
            for k, v in r.details.items():
                lines.append(f"   {k}: {v}")
    return "\n".join(lines)


class DataValidator:
    """数据验证器"""

    def __init__(self, context: CheckContext):
        self.context = context
        self.results: List[CheckResult] = []

    def validate(self, validator_names: List[str] = None) -> bool:
        """执行验证，返回是否全部通过"""
        self.results = run_validators(self.context, validator_names)
        return not any(r.level == CheckLevel.ERROR for r in self.results)

    def validate_and_report(self, validator_names: List[str] = None) -> bool:
        """执行验证并打印报告"""
        passed = self.validate(validator_names)
        report = format_report(self.results)
        logger.info("验证报告:\n%s", report)
        return passed

    def get_errors(self) -> List[CheckResult]:
        return [r for r in self.results if r.level == CheckLevel.ERROR]

    def get_warnings(self) -> List[CheckResult]:
        return [r for r in self.results if r.level == CheckLevel.WARNING]


# ==================== 内置验证器 ====================


@register_validator("directories_exist")
def check_directories(ctx: CheckContext) -> List[CheckResult]:
    """检查必要目录是否存在"""
    results = []

    if ctx.annotations_dir:
        if ctx.annotations_dir.exists():
            results.append(CheckResult(
                level=CheckLevel.PASS,
                message=f"标注目录存在: {ctx.annotations_dir}",
            ))
        else:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"标注目录不存在: {ctx.annotations_dir}",
            ))

    if ctx.images_dir:
        if ctx.images_dir.exists():
            results.append(CheckResult(
                level=CheckLevel.PASS,
                message=f"图片目录存在: {ctx.images_dir}",
            ))
        else:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"图片目录不存在: {ctx.images_dir}",
            ))

    return results


@register_validator("model_file")
def check_model_file(ctx: CheckContext) -> List[CheckResult]:
    """检查模型文件是否存在"""
    results = []

    if ctx.model_path:
        if ctx.model_path.exists():
            size_mb = ctx.model_path.stat().st_size / (1024 * 1024)
            results.append(CheckResult(
                level=CheckLevel.PASS,
                message=f"模型文件存在: {ctx.model_path.name} ({size_mb:.1f}MB)",
            ))
        else:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"模型文件不存在: {ctx.model_path}",
            ))

    if ctx.model_dir:
        if ctx.model_dir.exists():
            pt_files = list(ctx.model_dir.glob("*.pt"))
            if pt_files:
                results.append(CheckResult(
                    level=CheckLevel.PASS,
                    message=f"模型目录包含 {len(pt_files)} 个模型文件",
                    details={"files": [f.name for f in pt_files]},
                ))
            else:
                results.append(CheckResult(
                    level=CheckLevel.WARNING,
                    message=f"模型目录为空: {ctx.model_dir}",
                ))
        else:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"模型目录不存在: {ctx.model_dir}",
            ))

    return results


@register_validator("annotation_files")
def check_annotation_files(ctx: CheckContext) -> List[CheckResult]:
    """检查标注文件"""
    results = []

    if not ctx.annotations_dir or not ctx.annotations_dir.exists():
        return results

    xml_files = list(ctx.annotations_dir.glob("*.xml"))
    if len(xml_files) == 0:
        results.append(CheckResult(
            level=CheckLevel.ERROR,
            message="未找到任何 XML 标注文件",
        ))
    else:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"找到 {len(xml_files)} 个 XML 标注文件",
            details={"count": len(xml_files)},
        ))

    return results


@register_validator("image_annotation_match")
def check_image_annotation_match(ctx: CheckContext) -> List[CheckResult]:
    """检查图片和标注文件是否匹配"""
    results = []

    if not ctx.annotations_dir or not ctx.images_dir:
        return results
    if not ctx.annotations_dir.exists() or not ctx.images_dir.exists():
        return results

    xml_stems = {f.stem for f in ctx.annotations_dir.glob("*.xml")}
    image_stems = set()
    for ext in ctx.image_extensions:
        image_stems.update(f.stem for f in ctx.images_dir.glob(f"*{ext}"))

    missing_images = xml_stems - image_stems
    missing_annotations = image_stems - xml_stems

    if missing_images:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"{len(missing_images)} 个标注文件缺少对应图片",
            details={"missing": list(missing_images)[:10]},
        ))

    if missing_annotations:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"{len(missing_annotations)} 个图片缺少对应标注",
            details={"missing": list(missing_annotations)[:10]},
        ))

    if not missing_images and not missing_annotations:
        matched = len(xml_stems & image_stems)
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"图片和标注文件完全匹配，共 {matched} 对",
        ))

    return results


@register_validator("class_validation")
def check_classes(ctx: CheckContext) -> List[CheckResult]:
    """检查标注中的类别是否有效"""
    import xml.etree.ElementTree as ET

    results = []

    if not ctx.annotations_dir or not ctx.annotations_dir.exists():
        return results

    classes_set = set(ctx.classes) if ctx.classes else None
    found_classes = set()
    unknown_classes = set()
    invalid_files = []

    for xml_file in list(ctx.annotations_dir.glob("*.xml"))[:100]:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for obj in root.findall("object"):
                name_elem = obj.find("name")
                if name_elem is not None:
                    class_name = name_elem.text
                    found_classes.add(class_name)
                    if classes_set and class_name not in classes_set:
                        unknown_classes.add(class_name)
        except Exception:
            invalid_files.append(xml_file.name)

    if found_classes:
        results.append(CheckResult(
            level=CheckLevel.INFO,
            message=f"数据集中发现的类别: {sorted(found_classes)}",
        ))

    if unknown_classes:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"发现未知类别: {sorted(unknown_classes)}",
        ))

    if invalid_files:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"无法解析的 XML 文件: {len(invalid_files)} 个",
        ))

    if not unknown_classes and not invalid_files and found_classes:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message="类别验证通过",
        ))

    return results
