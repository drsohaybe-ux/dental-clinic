"""Update treatments price_snapshot, planned sessions, and patient earned entries to realistic Algerian market prices in DZD.

cat_0005 migrated treatment catalog items, catalog item sessions, invoices, payments,
and budgets. However, treatments.price_snapshot, planned_treatment_item_sessions.amount,
and patient_earned_entries.amount were not updated, leaving patient earned ledgers,
clinic receivables, aging reports, and doctor production at legacy Euro values (30, 75, 120, etc.).

This migration updates:
1. treatments.price_snapshot matching treatment_catalog_items.default_price
2. planned_treatment_item_sessions.amount matching catalog_item_sessions.default_price (for multi-session)
   or treatment_catalog_items.default_price (for single-session)
3. patient_earned_entries.amount matching planned_treatment_item_sessions.amount or catalog_item.default_price
   or treatments.price_snapshot

Revision ID: cat_0006
Revises: cat_0005
Create Date: 2026-09-13
"""

from collections.abc import Sequence
from alembic import op

revision: str = "cat_0006"
down_revision: str | None = "cat_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update treatments price_snapshot from treatment_catalog_items default_price
    op.execute("""
        UPDATE treatments t
        SET price_snapshot = tci.default_price
        FROM treatment_catalog_items tci
        WHERE t.catalog_item_id = tci.id
          AND tci.default_price IS NOT NULL
          AND t.clinic_id IN (
              SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          );
    """)

    # 2. Update multi-session planned treatment item sessions from catalog_item_sessions
    op.execute("""
        UPDATE planned_treatment_item_sessions ptis
        SET amount = cis.default_price
        FROM planned_treatment_items pti
        JOIN treatments t ON pti.treatment_id = t.id
        JOIN catalog_item_sessions cis ON cis.catalog_item_id = t.catalog_item_id AND cis.sequence = ptis.sequence
        WHERE ptis.plan_item_id = pti.id
          AND cis.default_price IS NOT NULL
          AND pti.clinic_id IN (
              SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          );
    """)

    # 3. Update single-session planned treatment item sessions from treatment_catalog_items
    op.execute("""
        UPDATE planned_treatment_item_sessions ptis
        SET amount = tci.default_price
        FROM planned_treatment_items pti
        JOIN treatments t ON pti.treatment_id = t.id
        JOIN treatment_catalog_items tci ON t.catalog_item_id = tci.id
        WHERE ptis.plan_item_id = pti.id
          AND tci.default_price IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM catalog_item_sessions cis
              WHERE cis.catalog_item_id = t.catalog_item_id AND cis.sequence = ptis.sequence
          )
          AND pti.clinic_id IN (
              SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          );
    """)

    # 4. Update patient_earned_entries from planned_treatment_item_sessions when source_session_id is present
    op.execute("""
        UPDATE patient_earned_entries pee
        SET amount = ptis.amount
        FROM planned_treatment_item_sessions ptis
        WHERE pee.source_session_id = ptis.id
          AND ptis.amount IS NOT NULL
          AND pee.clinic_id IN (
              SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          );
    """)

    # 5. Backfill catalog_item_id on patient_earned_entries from treatments if missing
    op.execute("""
        UPDATE patient_earned_entries pee
        SET catalog_item_id = t.catalog_item_id
        FROM treatments t
        WHERE pee.treatment_id = t.id
          AND pee.catalog_item_id IS NULL
          AND t.catalog_item_id IS NOT NULL
          AND pee.clinic_id IN (
              SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          );
    """)

    # 6. Update patient_earned_entries from treatment_catalog_items when source_session_id is NULL
    op.execute("""
        UPDATE patient_earned_entries pee
        SET amount = tci.default_price
        FROM treatment_catalog_items tci
        WHERE pee.catalog_item_id = tci.id
          AND pee.source_session_id IS NULL
          AND tci.default_price IS NOT NULL
          AND pee.clinic_id IN (
              SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          );
    """)

    # 7. Fallback: update patient_earned_entries from treatments price_snapshot when catalog_item_id was NULL

    op.execute("""
        UPDATE patient_earned_entries pee
        SET amount = t.price_snapshot
        FROM treatments t
        WHERE pee.treatment_id = t.id
          AND pee.source_session_id IS NULL
          AND pee.catalog_item_id IS NULL
          AND t.price_snapshot IS NOT NULL
          AND pee.clinic_id IN (
              SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          );
    """)


def downgrade() -> None:
    pass
