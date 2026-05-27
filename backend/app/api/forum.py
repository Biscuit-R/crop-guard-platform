import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import User, ForumPost, ForumComment
from app.models.schemas import (
    ForumPostListResponse,
    ForumPostResponse,
    ForumPostItem,
    ForumCommentItem,
    TokenResponse,
    AdminReviewRequest,
)
from app.utils.auth_utils import get_current_user, get_current_admin
from app.utils.file_utils import save_upload_file, get_file_url
from app.config import settings
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forum", tags=["讨论区"])

FORUM_IMAGE_DIR = os.path.join(settings.STATIC_DIR, "forum_images")
os.makedirs(FORUM_IMAGE_DIR, exist_ok=True)


def _build_post_item(post: ForumPost, include_comments: bool = False) -> ForumPostItem:
    item = ForumPostItem(
        id=post.id,
        user_id=post.user_id,
        content=post.content,
        image_url=post.image_url,
        status=post.status,
        is_pinned=post.is_pinned,
        admin_note=post.admin_note,
        username=post.user.username if post.user else "unknown",
        comment_count=len(post.comments),
        created_at=post.created_at,
    )
    if include_comments:
        item.comments = [
            ForumCommentItem(
                id=c.id,
                content=c.content,
                username=c.user.username if c.user else "unknown",
                created_at=c.created_at,
            )
            for c in post.comments
        ]
    return item


# ==================== 用户端接口 ====================


@router.get("/posts", response_model=ForumPostListResponse)
async def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    pinned_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ForumPost).filter(ForumPost.status == "approved")
    if pinned_only:
        query = query.filter(ForumPost.is_pinned == True)
    total = query.count()
    posts = (
        query.order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ForumPostListResponse(
        success=True,
        message="获取成功",
        data=[_build_post_item(p) for p in posts],
        total=total,
    )


@router.post("/posts", response_model=ForumPostResponse)
async def create_post(
    content: str = Form(...),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image_url = None
    if image and image.filename:
        filename = await save_upload_file(image, FORUM_IMAGE_DIR, max_size=10 * 1024 * 1024)
        image_url = get_file_url(filename, FORUM_IMAGE_DIR)

    post = ForumPost(
        user_id=current_user.id,
        content=content,
        image_url=image_url,
        status="pending",
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return ForumPostResponse(
        success=True,
        message="发布成功，等待管理员审核",
        data=_build_post_item(post),
    )


@router.get("/posts/{post_id}", response_model=ForumPostResponse)
async def get_post_detail(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")

    # 非管理员只能看 approved 的帖子
    if post.status != "approved" and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="帖子未通过审核")

    return ForumPostResponse(
        success=True,
        message="获取成功",
        data=_build_post_item(post, include_comments=True),
    )


@router.post("/posts/{post_id}/comments", response_model=TokenResponse)
async def create_comment(
    post_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(ForumPost).filter(ForumPost.id == post_id, ForumPost.status == "approved").first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")

    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="评论内容不能为空")

    comment = ForumComment(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
    )
    db.add(comment)
    db.commit()

    return TokenResponse(success=True, message="评论成功")


# ==================== 管理员接口 ====================


@router.get("/admin/posts", response_model=ForumPostListResponse)
async def admin_get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status_filter: str = Query("pending", alias="status"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(ForumPost).filter(ForumPost.status == status_filter)
    total = query.count()
    posts = (
        query.order_by(ForumPost.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ForumPostListResponse(
        success=True,
        message="获取成功",
        data=[_build_post_item(p) for p in posts],
        total=total,
    )


@router.put("/admin/posts/{post_id}/review", response_model=TokenResponse)
async def admin_review_post(
    post_id: int,
    body: AdminReviewRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")

    post.status = body.status
    post.admin_note = body.note
    db.commit()

    return TokenResponse(success=True, message=f"审核{'通过' if body.status == 'approved' else '拒绝'}")


@router.put("/admin/posts/{post_id}/pin", response_model=TokenResponse)
async def admin_pin_post(
    post_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")

    post.is_pinned = not post.is_pinned
    db.commit()

    return TokenResponse(success=True, message="已置顶" if post.is_pinned else "已取消置顶", data={"is_pinned": post.is_pinned})


@router.delete("/posts/{post_id}", response_model=TokenResponse)
async def delete_own_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能删除自己发布的帖子")

    # 删除关联图片
    if post.image_url:
        image_path = os.path.join(FORUM_IMAGE_DIR, os.path.basename(post.image_url))
        if os.path.exists(image_path):
            os.remove(image_path)

    db.query(ForumComment).filter(ForumComment.post_id == post_id).delete()
    db.delete(post)
    db.commit()

    return TokenResponse(success=True, message="帖子已删除")


@router.delete("/admin/posts/{post_id}", response_model=TokenResponse)
async def admin_delete_post(
    post_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")

    if post.image_url:
        image_path = os.path.join(FORUM_IMAGE_DIR, os.path.basename(post.image_url))
        if os.path.exists(image_path):
            os.remove(image_path)

    db.query(ForumComment).filter(ForumComment.post_id == post_id).delete()
    db.delete(post)
    db.commit()

    return TokenResponse(success=True, message="帖子已删除")
