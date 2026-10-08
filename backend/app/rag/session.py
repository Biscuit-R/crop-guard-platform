"""问答会话记忆（短期记忆 = 带过期时间的 Redis 会话缓存）。

为什么放 Redis 而不是服务端内存 / 数据库：
- 服务无状态可水平扩展，多 worker 不共享内存；
- 短期记忆天然带 TTL，30 分钟不说话即过期，无需定时清理任务；
- 一轮对话就是一次 GET + 一次 SETEX，成本可忽略。

MAX_TURNS 截断防止超长会话把 prompt 撑爆（只保留最近 N 轮）。
"""

import json

SESSION_PREFIX = "qa:session:"
SESSION_TTL_SECONDS = 30 * 60
MAX_TURNS = 5


def load_history(redis, session_id: str) -> list[dict]:
    raw = redis.get(SESSION_PREFIX + session_id)
    if not raw:
        return []
    try:
        turns = json.loads(raw)
    except (ValueError, TypeError):
        return []
    return turns if isinstance(turns, list) else []


def save_turn(redis, session_id: str, question: str, mode: str, answer_text: str) -> None:
    turns = load_history(redis, session_id)
    turns.append({"q": question, "mode": mode, "a": answer_text})
    turns = turns[-MAX_TURNS:]
    redis.set(
        SESSION_PREFIX + session_id,
        json.dumps(turns, ensure_ascii=False),
        ex=SESSION_TTL_SECONDS,
    )
