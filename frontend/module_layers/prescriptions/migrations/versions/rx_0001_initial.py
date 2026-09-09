"""rx_0001_initial — prescriptions and prescription_items tables.

Own Alembic branch (``prescriptions``): no down_revision, independent branch.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "rx_0001"
down_revision = None
branch_labels = ("prescriptions",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prescriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "clinic_id",
            UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("doctor_name_fr", sa.String(length=150), nullable=False, server_default="Dr. LOKMANE R."),
        sa.Column("doctor_specialty_fr", sa.String(length=150), nullable=False, server_default="Chirurgien Dentiste"),
        sa.Column("doctor_name_ar", sa.String(length=150), nullable=False, server_default="الدكتور لقمان ر."),
        sa.Column("doctor_specialty_ar", sa.String(length=150), nullable=False, server_default="جراح أسنان"),
        sa.Column("city", sa.String(length=100), nullable=False, server_default="Boumerdès"),
        sa.Column("prescription_date", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_prescriptions_clinic_id", "prescriptions", ["clinic_id"])
    op.create_index("ix_prescriptions_patient_id", "prescriptions", ["patient_id"])
    op.create_index("ix_prescriptions_is_active", "prescriptions", ["is_active"])

    op.create_table(
        "prescription_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "prescription_id",
            UUID(as_uuid=True),
            sa.ForeignKey("prescriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("medication_name", sa.String(length=200), nullable=False),
        sa.Column("dosage", sa.String(length=100), nullable=True),
        sa.Column("form", sa.String(length=100), nullable=True),
        sa.Column("frequency", sa.String(length=200), nullable=True),
        sa.Column("duration", sa.String(length=100), nullable=True),
        sa.Column("instructions", sa.String(length=500), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_prescription_items_prescription_id", "prescription_items", ["prescription_id"])


def downgrade() -> None:
    op.drop_index("ix_prescription_items_prescription_id", table_name="prescription_items")
    op.drop_table("prescription_items")
    op.drop_index("ix_prescriptions_is_active", table_name="prescriptions")
    op.drop_index("ix_prescriptions_patient_id", table_name="prescriptions")
    op.drop_index("ix_prescriptions_clinic_id", table_name="prescriptions")
    op.drop_table("prescriptions")
