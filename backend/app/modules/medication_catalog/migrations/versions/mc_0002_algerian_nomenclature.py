"""mc_0002_algerian_nomenclature — algerian_medications table.

Stores the official Algerian National Medication Nomenclature (~4,636 items)
for fast lookup, dental-prioritized auto-suggestions, and one-click additions
to clinic medication catalogs.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "mc_0002"
down_revision = "mc_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "algerian_medications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("registration_number", sa.String(length=100), nullable=True),
        sa.Column("brand_name", sa.String(length=200), nullable=False),
        sa.Column("dci", sa.String(length=250), nullable=False),
        sa.Column("form", sa.String(length=100), nullable=True),
        sa.Column("standard_form", sa.String(length=50), nullable=False, server_default="tablet"),
        sa.Column("dosage", sa.String(length=350), nullable=True),
        sa.Column("dose", sa.String(length=50), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("packaging", sa.String(length=500), nullable=True),
        sa.Column("laboratory", sa.String(length=200), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("price", sa.String(length=150), nullable=True),
        sa.Column("reimbursement", sa.String(length=50), nullable=True),
        sa.Column("is_dental", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_prescription", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_algerian_medications_brand_name", "algerian_medications", ["brand_name"])
    op.create_index("ix_algerian_medications_dci", "algerian_medications", ["dci"])
    op.create_index("ix_algerian_medications_is_dental", "algerian_medications", ["is_dental"])
    op.create_index(
        "ix_algerian_medications_reg_num", "algerian_medications", ["registration_number"]
    )


def downgrade() -> None:
    op.drop_index("ix_algerian_medications_reg_num", table_name="algerian_medications")
    op.drop_index("ix_algerian_medications_is_dental", table_name="algerian_medications")
    op.drop_index("ix_algerian_medications_dci", table_name="algerian_medications")
    op.drop_index("ix_algerian_medications_brand_name", table_name="algerian_medications")
    op.drop_table("algerian_medications")
