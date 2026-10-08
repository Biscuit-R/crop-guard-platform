"""RAG 知识问答路由（入口②：症状描述 → 检索 → 生成）。

端点保持薄：依赖注入组装真实链路，测试用 dependency_overrides 换假件。
encoder 用模块级缓存 —— BGE 模型加载是秒级开销，不能每个请求都来一次。
"""

import uuid
from collections.abc import Callable
from dataclasses import asdict
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal, get_db
from app.modules.auth.deps import get_redis
from app.rag import session as qa_session
from app.rag.direct import pest_profile
from app.rag.embedding import BGEEncoder
from app.rag.llm import DeepSeekClient
from app.rag.qa import QAResult, answer
from app.rag.rewrite import make_rewriter
from app.rag.retriever import DEFAULT_TOP_K, retrieve

router = APIRouter(tags=["rag"])

QAFunc = Callable[..., QAResult]


@lru_cache
def get_encoder() -> BGEEncoder:
    return BGEEncoder()


def get_qa() -> QAFunc:
    """组装真实链路：检索 + 三档阈值 + DeepSeek 生成。key 未配置时生成必失败，
    由 qa.answer 捕获走 fail-open —— 但配置缺失属于部署错误，这里显式 fail-closed。"""
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置：RAG 问答不可用")
    encoder = get_encoder()
    llm = DeepSeekClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.deepseek_timeout,
    )
    high, low = settings.retrieval_high, settings.retrieval_low
    rewriter = make_rewriter(llm.chat_raw)  # 每轮改写：口语规范化 + 指代消解（见 rewrite.py）

    def qa(query: str, history: list[dict] | None = None, prev_mode: str | None = None) -> QAResult:
        def retr(q: str, k: int) -> list:
            session = SessionLocal()
            try:
                return retrieve(session, encoder, q, k)
            finally:
                session.close()

        # 传客户端实例而非 generate 方法：低分澄清分支需要实例上的 chat_raw
        return answer(query, retr, llm, high, low, top_k=DEFAULT_TOP_K,
                      history=history, prev_mode=prev_mode, rewriter=rewriter)

    return qa


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=200)
    # 客户端首次不传，服务端生成；后续轮次带回即可续上会话记忆
    session_id: str | None = Field(default=None, max_length=64)


@router.post("/rag/ask")
def ask(payload: AskIn, qa: QAFunc = Depends(get_qa), redis=Depends(get_redis)) -> dict:
    # 非法 session_id 一律当新会话处理（服务端生成），不报错。
    # 超长（>64）进不了这里 —— AskIn 的 pydantic max_length 先拦为 422。
    session_id = payload.session_id
    if not session_id or not session_id.isalnum():
        session_id = uuid.uuid4().hex

    history = qa_session.load_history(redis, session_id)
    prev_mode = history[-1]["mode"] if history else None

    result = qa(payload.question, history=history, prev_mode=prev_mode)

    qa_session.save_turn(redis, session_id, payload.question, result.mode, result.answer)
    out = asdict(result)
    out["session_id"] = session_id
    return out


# ---- 入口①（D12）：检测 class_name → 查表直出，不过 LLM ----

@router.get("/rag/pests")
def pest_list() -> list[dict]:
    """图鉴全量（前端图鉴页 / 检测浮窗数据源）。纯内存数据，无库查询。"""
    from app.data.pest_database import PEST_DATABASE
    return PEST_DATABASE


@router.get("/rag/pests/{class_name}")
def pest(class_name: str, db: Session = Depends(get_db)) -> dict:
    profile = pest_profile(db, class_name)
    if profile is None:
        raise HTTPException(404, "未收录的虫害")
    return profile
