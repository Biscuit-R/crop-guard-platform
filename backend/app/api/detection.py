import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.detection_service import detection_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.utils.auth_utils import get_current_user
from app.database import get_db
from app.models.db_models import User, DetectionHistory
from app.config import settings
from app.models.schemas import SingleDetectionResponse, PestListResponse, PestItem

router = APIRouter(prefix="/detection", tags=["detection"])

ensure_directories()


@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),
    model_name: str = Form("pest-v1"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        image_path = os.path.join(settings.UPLOAD_DIR, filename)

        result = detection_service.detect_single_image(image_path, model_name)

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


@router.get("/pests/list", response_model=PestListResponse)
async def get_pest_list():
    pests = [
        PestItem(id=0, name="leaf_blight", chinese_name="叶斑病", category="真菌病害", description="叶片出现褐色或黑色斑点，严重时导致叶片枯死"),
        PestItem(id=1, name="rust", chinese_name="锈病", category="真菌病害", description="叶片背面出现铁锈色孢子堆，影响光合作用"),
        PestItem(id=2, name="powdery_mildew", chinese_name="白粉病", category="真菌病害", description="叶片表面覆盖白色粉状霉层"),
        PestItem(id=3, name="aphid", chinese_name="蚜虫", category="虫害", description="吸食植物汁液，导致叶片卷曲、发黄"),
        PestItem(id=4, name="caterpillar", chinese_name="毛虫", category="虫害", description="啃食叶片，造成缺刻或孔洞"),
        PestItem(id=5, name="leaf_miner", chinese_name="潜叶蝇", category="虫害", description="幼虫在叶片内部取食，形成蜿蜒隧道"),
        PestItem(id=6, name="bacterial_spot", chinese_name="细菌性斑点", category="细菌病害", description="叶片出现水渍状小斑点，后期变为褐色"),
        PestItem(id=7, name="mosaic_virus", chinese_name="花叶病毒", category="病毒病害", description="叶片出现黄绿相间的花叶症状，植株矮化"),
    ]
    return PestListResponse(
        success=True,
        message="获取成功",
        data=pests
    )
