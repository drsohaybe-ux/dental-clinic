"""Update catalog items and demo data to realistic Algerian market prices in DZD.

Migrates all treatment catalog prices to Algerian market references in DZD,
updates session distributions, converts clinic currency from EUR to DZD,
and updates demo budgets, invoices, payments, and invoice payments so
all dashboard revenue, KPIs, and overdue figures reflect realistic DZD figures.

Revision ID: cat_0005
Revises: cat_0004
Create Date: 2026-09-13
"""

from collections.abc import Sequence
from alembic import op

revision: str = "cat_0005"
down_revision: str | None = "cat_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update clinic currency to DZD
    op.execute("""
        UPDATE clinics
        SET currency = 'DZD'
        WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
           OR currency = 'EUR';
    """)

    # 2. Update treatment catalog items to Algerian DZD prices
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2000.0 WHERE internal_code = 'DX-VISIT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 1000.0 WHERE internal_code = 'DX-REVIEW' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 800.0 WHERE internal_code = 'DX-RXPA' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'DX-RXPAN' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 12000.0 WHERE internal_code = 'DX-CBCT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 6000.0 WHERE internal_code = 'DX-STUDY' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2000.0 WHERE internal_code = 'DX-PHOTO' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'DX-URGENT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2500.0 WHERE internal_code = 'DX-2ND-OPINION' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'DX-TELE' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 4000.0 WHERE internal_code = 'PREV-CLEAN' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2000.0 WHERE internal_code = 'PREV-FLUOR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 1000.0 WHERE internal_code = 'PREV-CHECKUP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2000.0 WHERE internal_code = 'PREV-SEAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 1000.0 WHERE internal_code = 'PREV-HYGIENE-EDU' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 7000.0 WHERE internal_code = 'PREV-CLEAN-CURETTAGE' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2500.0 WHERE internal_code = 'PREV-CLEAN-PED' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3500.0, surface_prices = '{"1": 3500.0, "2": 5500.0, "3": 7000.0, "4": 8000.0, "5": 9000.0}'::jsonb WHERE internal_code = 'REST-COMP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0, surface_prices = '{"1": 3000.0, "2": 4500.0, "3": 6000.0, "4": 7000.0, "5": 8000.0}'::jsonb WHERE internal_code = 'REST-AMAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 1500.0 WHERE internal_code = 'REST-TEMP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 10000.0 WHERE internal_code = 'REST-INLAY-COMP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 16000.0 WHERE internal_code = 'REST-INLAY-CER' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 12000.0 WHERE internal_code = 'REST-OVER-COMP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 18000.0 WHERE internal_code = 'REST-OVER-CER' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 15000.0 WHERE internal_code = 'REST-VEN-COMP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 35000.0 WHERE internal_code = 'REST-VEN-PORC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 35000.0 WHERE internal_code = 'REST-VEN-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 18000.0 WHERE internal_code = 'REST-CROWN-MC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 32000.0 WHERE internal_code = 'REST-CROWN-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 35000.0 WHERE internal_code = 'REST-CROWN-DISI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 12000.0 WHERE internal_code = 'REST-CROWN-METAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 4000.0 WHERE internal_code = 'REST-CROWN-PROV' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 35000.0 WHERE internal_code = 'REST-CROWN-IMPL-MC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 45000.0 WHERE internal_code = 'REST-CROWN-IMPL-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8000.0 WHERE internal_code = 'REST-CROWN-IMPL-PROV' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 18000.0, pricing_config = '{"pillar": 18000.0, "pontic": 14000.0}'::jsonb WHERE internal_code = 'REST-BRIDGE-MC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 32000.0, pricing_config = '{"pillar": 32000.0, "pontic": 25000.0}'::jsonb WHERE internal_code = 'REST-BRIDGE-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 20000.0, pricing_config = '{"pillar": 20000.0, "pontic": 15000.0}'::jsonb WHERE internal_code = 'REST-BRIDGE-MARY' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 15000.0 WHERE internal_code = 'REST-SPLINT-OCC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 5000.0 WHERE internal_code = 'REST-SPLINT-PERIO' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 7000.0 WHERE internal_code = 'REST-RECONSTR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'REST-FILL-REPAIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'REST-CROWN-RECEMENT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 20000.0 WHERE internal_code = 'REST-CROWN-POST-ENDO' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8000.0 WHERE internal_code = 'REST-HEAL-ABUT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 15000.0 WHERE internal_code = 'REST-DEF-ABUT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 6000.0 WHERE internal_code = 'ENDO-UNI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8500.0 WHERE internal_code = 'ENDO-BI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 12000.0 WHERE internal_code = 'ENDO-MULTI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 15000.0 WHERE internal_code = 'ENDO-RETREAT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 5000.0 WHERE internal_code = 'ENDO-POST-FIBER' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8000.0 WHERE internal_code = 'ENDO-POST-METAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3500.0 WHERE internal_code = 'ENDO-URGENT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2500.0 WHERE internal_code = 'ENDO-MED-REFRESH' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 12000.0 WHERE internal_code = 'ENDO-APICOFORM' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 5000.0 WHERE internal_code = 'ENDO-PED' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 4000.0 WHERE internal_code = 'PERIO-SCAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 6000.0 WHERE internal_code = 'PERIO-RAR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 20000.0 WHERE internal_code = 'PERIO-SURG' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 18000.0 WHERE internal_code = 'PERIO-GRAFT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 25000.0 WHERE internal_code = 'PERIO-BONE' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 4000.0 WHERE internal_code = 'PERIO-MAINT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 5000.0 WHERE internal_code = 'PERIO-CURET-SEXT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'PERIO-STUDY' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 7000.0 WHERE internal_code = 'PERIO-SPLINT-RAR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8000.0 WHERE internal_code = 'PERIO-GINGIV' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 22000.0 WHERE internal_code = 'PERIO-SURG-RESECT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 28000.0 WHERE internal_code = 'PERIO-SURG-REGEN' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'SURG-EXT-SIMPLE' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 6000.0 WHERE internal_code = 'SURG-EXT-COMPLEX' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 12000.0 WHERE internal_code = 'SURG-EXT-3MOLAR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 14000.0 WHERE internal_code = 'SURG-EXT-OST' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 75000.0 WHERE internal_code = 'SURG-IMP-TI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 95000.0 WHERE internal_code = 'SURG-IMP-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 40000.0 WHERE internal_code = 'SURG-SINUS' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 22000.0 WHERE internal_code = 'SURG-BONE-GRAFT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 15000.0 WHERE internal_code = 'SURG-APEC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8000.0 WHERE internal_code = 'SURG-FREN' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 10000.0 WHERE internal_code = 'SURG-BIOPSY' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 20000.0 WHERE internal_code = 'SURG-CONN-GRAFT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 18000.0 WHERE internal_code = 'SURG-CROWN-LENGTH' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 25000.0 WHERE internal_code = 'SURG-CYST' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 12000.0 WHERE internal_code = 'SURG-EXT-INCLUIDO' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 10000.0 WHERE internal_code = 'SURG-BONE-REGUL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8000.0 WHERE internal_code = 'SURG-PRP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 20000.0 WHERE internal_code = 'SURG-PERIIMP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 35000.0 WHERE internal_code = 'SURG-BONE-VERT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 30000.0 WHERE internal_code = 'SURG-BONE-HORIZ' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 25000.0 WHERE internal_code = 'SURG-SINUS-CLOSED' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 120000.0 WHERE internal_code = 'ORTO-METAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 160000.0 WHERE internal_code = 'ORTO-CERAM' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 250000.0 WHERE internal_code = 'ORTO-LINGUAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 180000.0 WHERE internal_code = 'ORTO-INV-LITE' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 280000.0 WHERE internal_code = 'ORTO-INV-FULL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2000.0 WHERE internal_code = 'ORTO-BRACK' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2000.0 WHERE internal_code = 'ORTO-REVIEW' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8000.0 WHERE internal_code = 'ORTO-RET-FIX' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 6000.0 WHERE internal_code = 'ORTO-RET-REM' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'ORTO-ATTACH' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 1500.0 WHERE internal_code = 'ORTO-BRACK-CEMENT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 6000.0 WHERE internal_code = 'ORTO-BRACK-DEBOND' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2500.0 WHERE internal_code = 'ORTO-SEPARATOR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 22000.0 WHERE internal_code = 'ORTO-PALATAL-EXP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 12000.0 WHERE internal_code = 'ORTO-TAD' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 15000.0 WHERE internal_code = 'EST-BLAN-AMB' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 25000.0 WHERE internal_code = 'EST-BLAN-CLIN' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 35000.0 WHERE internal_code = 'EST-BLAN-COMBO' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 6000.0 WHERE internal_code = 'EST-MICROAB' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 4000.0 WHERE internal_code = 'EST-REMIN' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 10000.0 WHERE internal_code = 'EST-COMP-AESTH' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 4500.0 WHERE internal_code = 'EST-PIG-REMOVE' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 40000.0 WHERE internal_code = 'PROT-FULL-SUP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 40000.0 WHERE internal_code = 'PROT-FULL-INF' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 55000.0 WHERE internal_code = 'PROT-PART-METAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 25000.0 WHERE internal_code = 'PROT-PART-ACR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 90000.0 WHERE internal_code = 'PROT-OVERDENT' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 6000.0 WHERE internal_code = 'PROT-REBASE' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 4000.0 WHERE internal_code = 'PROT-REPAIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 18000.0 WHERE internal_code = 'PROT-PROV-REMOV' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 3000.0 WHERE internal_code = 'PROT-OCC-ADJ' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 1500.0 WHERE internal_code = 'PED-FLUOR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 1500.0 WHERE internal_code = 'PED-SEAL' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 7000.0 WHERE internal_code = 'PED-PULPOTOMY' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8500.0 WHERE internal_code = 'PED-CROWN-SS' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 7500.0 WHERE internal_code = 'PED-SPACE' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 11000.0 WHERE internal_code = 'PED-SPACE-COMPOUND' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2500.0 WHERE internal_code = 'PED-EXT-TEMP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 2500.0, surface_prices = '{"1": 2500.0, "2": 3500.0, "3": 4500.0, "4": 5000.0, "5": 5500.0}'::jsonb WHERE internal_code = 'PED-FILL-TEMP' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")
    op.execute("""UPDATE treatment_catalog_items SET default_price = 8000.0 WHERE internal_code = 'PED-PULPECTOMY' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');""")

    # 3. Update catalog item sessions
    op.execute("""UPDATE catalog_item_sessions SET default_price = 10000.0 WHERE sequence = 1 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-MC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 8000.0 WHERE sequence = 2 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-MC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 18000.0 WHERE sequence = 1 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 14000.0 WHERE sequence = 2 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 20000.0 WHERE sequence = 1 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-DISI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 15000.0 WHERE sequence = 2 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-DISI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 20000.0 WHERE sequence = 1 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-IMPL-MC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 15000.0 WHERE sequence = 2 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-IMPL-MC' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 25000.0 WHERE sequence = 1 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-IMPL-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 20000.0 WHERE sequence = 2 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'REST-CROWN-IMPL-ZIR' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 4000.0 WHERE sequence = 1 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'ENDO-MULTI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 4000.0 WHERE sequence = 2 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'ENDO-MULTI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 4000.0 WHERE sequence = 3 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'ENDO-MULTI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 50000.0 WHERE sequence = 1 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'SURG-IMP-TI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 10000.0 WHERE sequence = 2 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'SURG-IMP-TI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")
    op.execute("""UPDATE catalog_item_sessions SET default_price = 15000.0 WHERE sequence = 3 AND catalog_item_id IN (SELECT id FROM treatment_catalog_items WHERE internal_code = 'SURG-IMP-TI' AND clinic_id IN (SELECT id FROM clinics WHERE currency IN ('DZD', 'EUR') OR id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));""")

    # 4. Update demo invoice items with new catalog prices
    op.execute("""
        UPDATE invoice_items ii
        SET unit_price = tci.default_price,
            line_subtotal = tci.default_price * ii.quantity,
            line_total = tci.default_price * ii.quantity
        FROM treatment_catalog_items tci
        WHERE ii.catalog_item_id = tci.id
          AND ii.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          AND tci.default_price IS NOT NULL;
    """)

    # 5. Update demo invoices total/subtotal from invoice items
    op.execute("""
        UPDATE invoices inv
        SET total = sub.new_total,
            subtotal = sub.new_total
        FROM (
            SELECT invoice_id, SUM(line_total) as new_total
            FROM invoice_items
            GROUP BY invoice_id
        ) sub
        WHERE inv.id = sub.invoice_id
          AND inv.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
    """)

    # 6. Update demo payments and invoice payments for paid/partial invoices
    op.execute("""
        UPDATE invoice_payments ip
        SET amount = inv.total
        FROM invoices inv
        WHERE ip.invoice_id = inv.id
          AND inv.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          AND inv.status = 'paid';
    """)

    op.execute("""
        UPDATE payments p
        SET amount = ip.amount,
            currency = 'DZD'
        FROM invoice_payments ip
        JOIN invoices inv ON ip.invoice_id = inv.id
        WHERE ip.payment_id = p.id
          AND inv.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          AND inv.status = 'paid';
    """)

    op.execute("""
        UPDATE payment_allocations pa
        SET amount = p.amount
        FROM payments p
        WHERE pa.payment_id = p.id
          AND p.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
    """)

    # Specific partial invoices updates:
    # FAC-2026-0002 (total 8500, paid 4250)
    op.execute("""
        UPDATE invoice_payments ip
        SET amount = 4250.00
        FROM invoices inv
        WHERE ip.invoice_id = inv.id
          AND inv.invoice_number = 'FAC-2026-0002'
          AND inv.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
    """)
    op.execute("""
        UPDATE payments p
        SET amount = 4250.00,
            currency = 'DZD'
        FROM invoice_payments ip
        JOIN invoices inv ON ip.invoice_id = inv.id
        WHERE ip.payment_id = p.id
          AND inv.invoice_number = 'FAC-2026-0002'
          AND inv.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
    """)

    # FAC-2026-0003 (total 30000, paid 15000)
    op.execute("""
        UPDATE invoice_payments ip
        SET amount = 15000.00
        FROM invoices inv
        WHERE ip.invoice_id = inv.id
          AND inv.invoice_number = 'FAC-2026-0003'
          AND inv.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
    """)
    op.execute("""
        UPDATE payments p
        SET amount = 15000.00,
            currency = 'DZD'
        FROM invoice_payments ip
        JOIN invoices inv ON ip.invoice_id = inv.id
        WHERE ip.payment_id = p.id
          AND inv.invoice_number = 'FAC-2026-0003'
          AND inv.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
    """)

    # 7. Update demo budget items with new catalog prices
    op.execute("""
        UPDATE budget_items bi
        SET unit_price = tci.default_price
        FROM treatment_catalog_items tci
        WHERE bi.catalog_item_id = tci.id
          AND bi.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
          AND tci.default_price IS NOT NULL;
    """)

    # 8. Update demo budgets total/subtotal from budget items
    op.execute("""
        UPDATE budgets b
        SET total = sub.new_total,
            subtotal = sub.new_total
        FROM (
            SELECT budget_id, SUM(unit_price * quantity) as new_total
            FROM budget_items
            GROUP BY budget_id
        ) sub
        WHERE b.id = sub.budget_id
          AND b.clinic_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
    """)


def downgrade() -> None:
    pass
