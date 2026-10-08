"""users + detection_records

Revision ID: 0001
Revises:
Create Date: 2026-10-08

手写迁移（autogenerate 需要连真库比对，Docker 未起时先落此版）。
字段与 app/modules/auth/models.py、app/modules/detection/models.py 一一对应；
模型再变时用 autogenerate 出增量迁移，此版不动。
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(32), nullable=False, unique=True),
        sa.Column("phone", sa.String(16)),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "detection_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("image_key", sa.String(256), nullable=False),
        sa.Column("result_key", sa.String(256)),
        sa.Column("model_name", sa.String(64), nullable=False, server_default=""),
        sa.Column("detections", sa.JSON()),
        sa.Column("error", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("detection_records")
    op.drop_table("users")
