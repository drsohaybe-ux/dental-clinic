"""add_is_urgent_to_chat_session_states

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-28 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely add is_urgent column to chat_session_states table
    op.add_column(
        'chat_session_states',
        sa.Column('is_urgent', sa.Boolean(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('chat_session_states', 'is_urgent')
