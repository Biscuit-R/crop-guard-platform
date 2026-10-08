"""应用配置。

所有配置从环境变量 / `.env` 读取，代码里不出现魔法值。
分组顺序与 `docs/decisions.md` 的基线表一致。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "crop-guard-platform"
    debug: bool = False

    # PostgreSQL
    # ⚠️ 默认值沿用了归档的弱口令，仅够本地跑通。
    #    「默认凭据上真实服务器」的处置推迟到阶段 5，见 docs/decisions.md。
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "crop_user"
    postgres_password: str = "crop_password"
    postgres_db: str = "crop_guard_db"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_db: int = 0

    # MinIO
    minio_endpoint: str = "localhost:9002"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "crop-guard"
    minio_secure: bool = False

    # DeepSeek（D7：云 LLM，OpenAI 兼容接口，换供应商只改 base_url + 模型名）
    deepseek_api_key: str = ""  # 空 = 未配置，RAG 问答不可用（fail-closed 到配置层）
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout: float = 30.0  # 挂住的 LLM 必须能转成 LLMError 走 fail-open，不能拖死请求

    # 阈值三档（D10）。2026-10-08 口语化改写评测集重测确认（草稿集 2026-10-05 定的值不变）：
    #   A 症状题 [0.6697, 0.8575] / B1 无关题上界 0.3754 / B2 上界 0.6383，三组不重叠；
    #   0.60/0.75 仍落在两组分界内 → 维持。B2 落点 n07/n10 拒答、n08/n09 中间档
    #   （拍板：B2 允许中间档，不强制）。
    retrieval_high: float = 0.75
    retrieval_low: float = 0.60

    # HF 镜像源：.env 里的值 pydantic 只读进 Settings，不进 os.environ；
    # 而 HF 库直接读环境变量 —— 由 embedding.py 在导入模型库前写入（见该文件注释）。
    hf_endpoint: str = ""

    # 检测
    model_path: str = "models/model_102.pt"
    max_upload_mb: int = 50  # 上限检查在嗅探之前：超限直接 413，不读内容

    # 短信验证码演示模式：不接真实短信网关，验证码随 /auth/sms/send 响应返回、
    # 由前端弹窗展示。生产必须置 false（code 不出接口，走真实网关下发）。
    sms_demo: bool = True

    # 账号（D6：PyJWT + 直接 bcrypt）。jwt_secret 沿用弱默认仅够本地跑通，
    # 「秘密来源」与默认凭据一并推迟到阶段 5（decisions.md 末尾清单）。
    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 720  # 凭据有效期可配置（验收标准）
    login_max_attempts: int = 5

    @property
    def database_url(self) -> str:
        """SQLAlchemy 连接串（同步驱动，见 D3）。"""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """带缓存的配置获取。测试里需要改配置时调用 `get_settings.cache_clear()`。"""
    return Settings()
