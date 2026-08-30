"""add_external_id_and_source_to_appointments

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-30 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add external_id and source columns to appointments
    op.add_column(
        'appointments',
        sa.Column('external_id', sa.String(255), nullable=True)
    )
    op.add_column(
        'appointments',
        sa.Column('source', sa.String(50), server_default='manual', nullable=False)
    )

    # 2. Create partial unique index on (clinic_id, external_id)
    op.create_index(
        'uq_appointments_clinic_external_id',
        'appointments',
        ['clinic_id', 'external_id'],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL")
    )


def downgrade() -> None:
    op.drop_index('uq_appointments_clinic_external_id', table_name='appointments')
    op.drop_column('appointments', 'source')
    op.drop_column('appointments', 'external_id')
