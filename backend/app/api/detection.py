import os
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.detection_service import detection_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.utils.auth_utils import get_current_user
from app.database import get_db
from app.models.db_models import User, DetectionHistory
from app.config import settings
from app.models.schemas import (
    SingleDetectionResponse, BatchDetectionResponse, VideoDetectionResponse, PestListResponse, PestItem,
    ModelStatusResponse, ModelStatus,
    ModelListResponse, ModelInfo,
    ModelSwitchRequest,
    VersionHistoryResponse, VersionHistoryItem,
)

router = APIRouter(prefix="/detection", tags=["detection"])

ensure_directories()


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

        history = DetectionHistory(
            user_id=current_user.id,
            filename=file.filename or filename,
            media_type="video",
            video_url=result.video_url,
            result_video_url=result.result_video_url,
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


@router.get("/pests/list", response_model=PestListResponse)
async def get_pest_list():
    pests = [
        # 真菌病害
        PestItem(id=1, name="leaf_blight", chinese_name="叶斑病", category="真菌病害", description="叶片出现褐色或黑色斑点，严重时导致叶片枯死"),
        PestItem(id=2, name="rust", chinese_name="锈病", category="真菌病害", description="叶片背面出现铁锈色孢子堆，影响光合作用"),
        PestItem(id=3, name="powdery_mildew", chinese_name="白粉病", category="真菌病害", description="叶片表面覆盖白色粉状霉层"),
        PestItem(id=4, name="anthracnose", chinese_name="炭疽病", category="真菌病害", description="叶片和果实出现凹陷的黑色病斑"),
        # 细菌病害
        PestItem(id=5, name="bacterial_spot", chinese_name="细菌性斑点", category="细菌病害", description="叶片出现水渍状小斑点，后期变为褐色"),
        PestItem(id=6, name="soft_rot", chinese_name="软腐病", category="细菌病害", description="组织软化腐烂，有恶臭气味"),
        PestItem(id=7, name="bacterial_wilt", chinese_name="青枯病", category="细菌病害", description="植株迅速萎蔫，维管束变褐"),
        # 病毒病害
        PestItem(id=8, name="mosaic_virus", chinese_name="花叶病毒", category="病毒病害", description="叶片出现黄绿相间的花叶症状，植株矮化"),
        PestItem(id=9, name="yellowing_virus", chinese_name="黄化病毒", category="病毒病害", description="叶片黄化，植株生长受阻"),
        # 虫害
        PestItem(id=10, name="aphid", chinese_name="蚜虫", category="虫害", description="吸食植物汁液，导致叶片卷曲、发黄"),
        PestItem(id=11, name="caterpillar", chinese_name="毛虫", category="虫害", description="啃食叶片，造成缺刻或孔洞"),
        PestItem(id=12, name="leaf_miner", chinese_name="潜叶蝇", category="虫害", description="幼虫在叶片内部取食，形成蜿蜒隧道"),
        PestItem(id=13, name="red_spider", chinese_name="红蜘蛛", category="虫害", description="吸食叶片汁液，出现密集白色小点"),
    ]
    return PestListResponse(
        success=True,
        message="获取成功",
        data=pests
    )
