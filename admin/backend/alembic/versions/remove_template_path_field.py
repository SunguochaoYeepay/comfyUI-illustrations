"""Remove template_path field from base_models table

Revision ID: remove_template_path
Revises: update_base_model_comprehensive
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_template_path'
down_revision = 'update_base_model_comprehensive'
branch_labels = None
depends_on = None


def upgrade():
    """移除 base_models 表中的 template_path 字段"""
    # 删除 template_path 列
    op.drop_column('base_models', 'template_path')


def downgrade():
    """回滚：重新添加 template_path 字段"""
    # 重新添加 template_path 列
    op.add_column('base_models', sa.Column('template_path', sa.String(500), nullable=True))
