import os
import time
import asyncio
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.services.detection_service import detection_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.utils.auth_utils import get_current_user
from app.database import get_db
from app.models.db_models import User, DetectionHistory
from app.config import settings, CHINESE_CLASS_NAMES
from app.models.schemas import (
    SingleDetectionResponse, BatchDetectionResponse, VideoDetectionResponse, PestListResponse, PestItem,
    ModelStatusResponse, ModelStatus,
    ModelListResponse, ModelInfo,
    ModelSwitchRequest,
    VersionHistoryResponse, VersionHistoryItem,
    FrameDetectionResponse, FrameDetectionResult,
)

router = APIRouter(prefix="/detection", tags=["detection"])

ensure_directories()

# 摄像头帧检测并发控制（最多同时处理 5 个请求）
_frame_semaphore = asyncio.Semaphore(5)


@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),
    model_name: str = Form("pest-v1"),
    conf: float = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        image_path = os.path.join(settings.UPLOAD_DIR, filename)

        actual_model = detection_service.current_model_version or model_name
        result = detection_service.detect_single_image(image_path, actual_model, conf=conf)

        history = DetectionHistory(
            user_id=current_user.id,
            filename=filename,
            original_image=result.image_url,
            result_image=result.result_image_url,
            model_name=result.model_name,
            total_objects=result.total_objects,
            detection_time=result.detection_time,
            boxes=[box.model_dump() for box in result.boxes],
            status="completed",
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        result_dict = result.model_dump()
        result_dict["detection_id"] = str(history.id)

        return SingleDetectionResponse(
            success=True,
            message="检测成功",
            data=result_dict
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.post("/batch", response_model=BatchDetectionResponse)
async def detect_batch_images(
    files: List[UploadFile] = File(...),
    model_name: str = Form("pest-v1"),
    conf: float = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    actual_model = detection_service.current_model_version or model_name
    results = []
    for file in files:
        try:
            filename = await save_upload_file(file, settings.UPLOAD_DIR)
            image_path = os.path.join(settings.UPLOAD_DIR, filename)
            result = detection_service.detect_single_image(image_path, actual_model, conf=conf)

            history = DetectionHistory(
                user_id=current_user.id,
                filename=filename,
                original_image=result.image_url,
                result_image=result.result_image_url,
                model_name=result.model_name,
                total_objects=result.total_objects,
                detection_time=result.detection_time,
                boxes=[box.model_dump() for box in result.boxes],
                status="completed",
            )
            db.add(history)
            db.commit()
            db.refresh(history)

            result_dict = result.model_dump()
            result_dict["detection_id"] = str(history.id)
            results.append({"filename": file.filename, "success": True, "data": result_dict})
        except Exception as e:
            results.append({"filename": file.filename, "success": False, "error": str(e)})

    return BatchDetectionResponse(
        success=True,
        message=f"批量检测完成，共 {len(results)} 张",
        data={"results": results, "total": len(results)}
    )


@router.post("/video", response_model=VideoDetectionResponse)
async def detect_video(
    file: UploadFile = File(...),
    model_name: str = Form("pest-v1"),
    conf: float = Form(None),
    frame_interval: int = Form(5, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        filename = await save_upload_file(file, settings.VIDEO_DIR, max_size=settings.VIDEO_MAX_SIZE)
        video_path = os.path.join(settings.VIDEO_DIR, filename)

        actual_model = detection_service.current_model_version or model_name
        result = detection_service.detect_video(video_path, actual_model, conf=conf, frame_interval=frame_interval)

        cover_url = result.key_frames[0] if result.key_frames else None
        history = DetectionHistory(
            user_id=current_user.id,
            filename=file.filename or filename,
            media_type="video",
            video_url=result.video_url,
            result_video_url=result.result_video_url,
            result_image=cover_url,
            frame_count=result.total_frames,
            fps=result.fps,
            duration=result.duration,
            model_name=result.model_name,
            total_objects=result.total_objects,
            detection_time=result.detection_time,
            boxes=[],
            status="completed",
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        result_dict = result.model_dump()
        result_dict["detection_id"] = str(history.id)

        return VideoDetectionResponse(
            success=True,
            message="视频检测成功",
            data=result_dict
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频检测失败: {str(e)}")


@router.get("/model/status", response_model=ModelStatusResponse)
async def get_model_status(current_user: User = Depends(get_current_user)):
    """获取当前模型状态"""
    status = detection_service.get_status()
    return ModelStatusResponse(
        success=True,
        message="获取成功",
        data=ModelStatus(**status)
    )


@router.post("/model/reload", response_model=ModelStatusResponse)
async def reload_model(current_user: User = Depends(get_current_user)):
    """手动重载模型"""
    status = detection_service.reload()
    return ModelStatusResponse(
        success=True,
        message="模型已重载",
        data=ModelStatus(**status)
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models(current_user: User = Depends(get_current_user)):
    """列出所有可用模型版本"""
    models = detection_service.list_models()
    return ModelListResponse(
        success=True,
        message="获取成功",
        data=models
    )


@router.post("/models/switch", response_model=ModelStatusResponse)
async def switch_model(request: ModelSwitchRequest, current_user: User = Depends(get_current_user)):
    """切换到指定版本的模型"""
    try:
        status = detection_service.switch_model(request.version)
        return ModelStatusResponse(
            success=True,
            message=f"已切换到版本 {status['model_version']}",
            data=ModelStatus(**status)
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型切换失败: {str(e)}")


@router.get("/models/history", response_model=VersionHistoryResponse)
async def get_model_history(current_user: User = Depends(get_current_user)):
    """获取训练版本历史"""
    history = detection_service.get_version_history()
    return VersionHistoryResponse(
        success=True,
        message="获取成功",
        data=history
    )


@router.post("/frame", response_model=FrameDetectionResponse)
async def detect_frame(
    file: UploadFile = File(...),
    model_name: str = Form("pest-v1"),
    conf: float = Form(None),
    current_user: User = Depends(get_current_user),
):
    """
    单帧实时检测（摄像头模式用）

    接收一帧图片（JPEG/PNG），返回检测框坐标和类别信息
    """
    if detection_service.model is None:
        return FrameDetectionResponse(
            success=False, message="模型未加载，请检查模型状态", data=None,
        )

    try:
        async with _frame_semaphore:
            start = time.time()
            content = await file.read()
            if not content or len(content) < 100:
                return FrameDetectionResponse(
                    success=False, message="图像数据为空或过小", data=None,
                )

            nparr = np.frombuffer(content, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                return FrameDetectionResponse(
                    success=False, message="无法解析图片帧", data=None,
                )

            results = detection_service.model.predict(
                source=frame,
                conf=conf if conf is not None else settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD,
                imgsz=640,
                save=False,
                verbose=False,
            )

            boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    en_name = detection_service.class_names.get(class_id, f"class_{class_id}")
                    cn_name = CHINESE_CLASS_NAMES.get(en_name, en_name)
                    boxes.append({
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": en_name,
                        "chinese_name": cn_name,
                    })

            detection_time = time.time() - start
            return FrameDetectionResponse(
                success=True,
                message="检测完成",
                data=FrameDetectionResult(
                    boxes=boxes,
                    total_objects=len(boxes),
                    detection_time=round(detection_time, 3),
                )
            )
    except Exception as e:
        return FrameDetectionResponse(
            success=False, message=f"帧检测失败: {str(e)}", data=None,
        )


@router.get("/pests/list", response_model=PestListResponse)
async def get_pest_list():
    from app.data.pest_database import PEST_DATABASE
    pests = [PestItem(id=i + 1, **item) for i, item in enumerate(PEST_DATABASE)]
    return PestListResponse(
        success=True,
        message="获取成功",
        data=pests
    )
