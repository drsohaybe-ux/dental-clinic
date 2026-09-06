"""add_social_media_insights

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0011'
down_revision: Union[str, None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'social_media_insights',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('account_id', sa.String(length=100), nullable=False, server_default='default'),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_followers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reach', sa.Integer(), server_default='0', nullable=False),
        sa.Column('profile_views', sa.Integer(), server_default='0', nullable=False),
        sa.Column('website_clicks', sa.Integer(), server_default='0', nullable=False),
        sa.Column('saves', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('platform', 'account_id', 'date', name='uq_social_insights_platform_account_date')
    )
    op.create_index(
        'idx_social_media_insights_platform_date',
        'social_media_insights',
        ['platform', 'date'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_social_media_insights_platform_date', table_name='social_media_insights')
    op.drop_table('social_media_insights')
