from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== 检测相关 Schema ====================

class DetectionBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str


class DetectionResult(BaseModel):
    detection_id: str
    image_url: str
    result_image_url: str
    boxes: List[DetectionBox]
    total_objects: int
    detection_time: float
    model_name: str
    created_at: datetime


class SingleDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DetectionResult] = None


class BatchDetectionItem(BaseModel):
    filename: str
    success: bool
    data: Optional[DetectionResult] = None
    error: Optional[str] = None


class BatchDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class VideoDetectionResult(BaseModel):
    detection_id: str
    video_url: str
    result_video_url: str
    total_objects: int
    total_frames: int
    processed_frames: int
    fps: float
    duration: float
    detection_time: float
    model_name: str
    created_at: datetime
    summary: dict  # {"class_name": count, ...}
    key_frames: List[str]  # 关键帧截图 URL


class VideoDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[VideoDetectionResult] = None


class PestItem(BaseModel):
    id: int
    name: str
    chinese_name: str
    category: str
    description: Optional[str] = None


class PestListResponse(BaseModel):
    success: bool
    message: str
    data: List[PestItem]


# ==================== 认证相关 Schema ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str = "user"
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# ==================== 历史记录 Schema ====================

class HistoryDetailItem(BaseModel):
    id: int
    filename: str
    media_type: str = "image"
    original_image: Optional[str] = None
    result_image: Optional[str] = None
    video_url: Optional[str] = None
    result_video_url: Optional[str] = None
    frame_count: Optional[int] = None
    fps: Optional[float] = None
    duration: Optional[float] = None
    model_name: Optional[str] = None
    total_objects: int = 0
    detection_time: Optional[float] = None
    boxes: Optional[List[DetectionBox]] = None
    status: str = "completed"
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    success: bool
    message: str
    data: List[HistoryDetailItem]
    total: int


# ==================== 看板统计 Schema ====================

class DashboardStats(BaseModel):
    today_detections: int
    today_objects: int
    today_users: int
    total_users: int


# ==================== 模型状态 Schema ====================

class ModelStatus(BaseModel):
    model_path: str
    model_version: str
    model_mtime: Optional[str] = None
    class_count: int
    is_loaded: bool


class ModelStatusResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[ModelStatus] = None


class ModelInfo(BaseModel):
    filename: str
    version: str
    size_mb: float
    modified_at: str
    is_current: bool
    display_name: str = ""
    description: str = ""


class ModelListResponse(BaseModel):
    success: bool
    message: str = ""
    data: List[ModelInfo] = []


class ModelSwitchRequest(BaseModel):
    version: str


class VersionHistoryItem(BaseModel):
    version: str
    created_at: str
    description: str = ""
    metrics: Optional[dict] = None


class VersionHistoryResponse(BaseModel):
    success: bool
    message: str = ""
    data: List[VersionHistoryItem] = []


# ==================== 讨论区 Schema ====================

class ForumPostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class ForumCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class ForumCommentItem(BaseModel):
    id: int
    content: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class ForumPostItem(BaseModel):
    id: int
    content: str
    image_url: Optional[str] = None
    status: str
    is_pinned: bool = False
    admin_note: Optional[str] = None
    username: str
    comment_count: int = 0
    created_at: datetime
    comments: Optional[List[ForumCommentItem]] = None

    class Config:
        from_attributes = True


class ForumPostListResponse(BaseModel):
    success: bool
    message: str = ""
    data: List[ForumPostItem] = []
    total: int = 0


class ForumPostResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[ForumPostItem] = None


class AdminReviewRequest(BaseModel):
    status: str = Field(..., pattern=r"^(approved|rejected)$")
    note: Optional[str] = Field(None, max_length=500)
