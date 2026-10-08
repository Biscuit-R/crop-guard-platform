"""users.phone 对齐 ORM 长度（String(20)）

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-08

验收发现的迁移/ORM 偏差：0001 建了 VARCHAR(16)，ORM 是 String(20)。
PhoneIn 校验 11 位手机号，20 留了区号等余量 —— 以 ORM 为准补一条增量迁移。
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "phone",
                    existing_type=sa.String(16), type_=sa.String(20))


def downgrade() -> None:
    op.alter_column("users", "phone",
                    existing_type=sa.String(20), type_=sa.String(16))
