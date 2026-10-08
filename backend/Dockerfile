# 多阶段：第一层只做依赖安装，源码变了不必重装依赖。
# uv 的官方镜像里已经带了 uv 本体，不需要额外 curl 装。
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# 先只拷清单 —— 这一层的缓存键就只有依赖定义，改代码不会让它失效。
# uv.lock 必须进镜像：它是环境可复现的依据（CLAUDE.md），--frozen 禁止顺手重解析。
COPY pyproject.toml uv.lock ./
COPY app/__init__.py ./app/
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# 起服务前先跑迁移 —— 表结构由 Alembic 负责，应用启动即幂等就绪
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
