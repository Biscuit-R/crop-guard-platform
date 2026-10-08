"""健康检查。

**故意分成两个端点** —— 这是需求里「推理中健康检查 p99 < 100ms」那条验收标准的前提：

- `/health`       存活探针。不碰任何外部依赖，只回答「进程还活着吗」。
                  推理占满线程池时它也必须立刻返回 —— 这正是它能测出问题的原因。
- `/health/ready` 就绪探针。真的去连数据库，失败返回 503，让编排层知道不能接流量。

如果把两者合成一个「顺手把数据库也 ping 一下」的端点，存活探针就会被数据库故障拖慢，
`p99 < 100ms` 那条标准也就测不出真正想测的东西了。
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        # 不给编排层抛 500 —— 就绪探针的语义是「返回状态」，不是「报错」。
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "down"}
    return {"status": "ok", "database": "up"}
