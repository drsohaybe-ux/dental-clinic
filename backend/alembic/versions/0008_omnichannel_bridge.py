"""add_omnichannel_bridge_tables

Revision ID: 0008_omnichannel_bridge
Revises: 0007_social_automation
Create Date: 2026-08-27 22:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Chat Messages Table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clinics.id'), nullable=True, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True, index=True),
        sa.Column('phone', sa.String(50), nullable=False, index=True),
        sa.Column('sender', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False, server_default='telegram'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Patient Leads Table
    op.create_table(
        'patient_leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clinics.id'), nullable=True, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(50), nullable=False, index=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='telegram'),
        sa.Column('stage', sa.String(50), nullable=False, server_default='new'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_converted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Patient Dossier Files Table
    op.create_table(
        'patient_dossier_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clinics.id'), nullable=True, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True, index=True),
        sa.Column('phone', sa.String(50), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False, server_default='xray_panoramic'),
        sa.Column('file_url', sa.Text(), nullable=False),
        sa.Column('ai_analysis', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending_consultation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. Chat Session States Table
    op.create_table(
        'chat_session_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clinics.id'), nullable=True, index=True),
        sa.Column('phone', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('is_human_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_takeover_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('chat_session_states')
    op.drop_table('patient_dossier_files')
    op.drop_table('patient_leads')
    op.drop_table('chat_messages')
