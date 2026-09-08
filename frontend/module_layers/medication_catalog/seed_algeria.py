"""Seeder for the Algerian National Medication Nomenclature (~4,636 items).

Loads normalized medication records from algerian_nomenclature.json into
the algerian_medications table. Fast (<2s) and idempotent: if records
already exist, skips or refreshes.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AlgerianMedication

DATA_FILE = Path(__file__).resolve().parent / "data" / "algerian_nomenclature.json"


def load_nomenclature_records() -> list[dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Nomenclature cache file not found at {DATA_FILE}")
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


async def seed_algerian_nomenclature(db: AsyncSession, force_refresh: bool = False) -> dict[str, int]:
    """Seed Algerian national nomenclature medications into the database.

    Idempotent: if rows already exist and force_refresh is False, returns
    existing total without re-inserting.
    """
    count_stmt = select(func.count(AlgerianMedication.id))
    existing_count = (await db.execute(count_stmt)).scalar() or 0

    if existing_count > 0 and not force_refresh:
        return {"seeded": 0, "total": existing_count}

    if force_refresh and existing_count > 0:
        from sqlalchemy import delete

        await db.execute(delete(AlgerianMedication))
        await db.flush()

    raw_items = load_nomenclature_records()
    total_raw = len(raw_items)

    # Batch insert in chunks of 500
    chunk_size = 500
    seeded = 0

    for i in range(0, total_raw, chunk_size):
        chunk = raw_items[i : i + chunk_size]
        items_to_add = []
        for item in chunk:
            items_to_add.append(
                AlgerianMedication(
                    id=UUID(item["id"]) if isinstance(item["id"], str) else item["id"],
                    code=item.get("code"),
                    registration_number=item.get("registration_number"),
                    brand_name=item["brand_name"],
                    dci=item["dci"],
                    form=item.get("form"),
                    standard_form=item.get("standard_form", "tablet"),
                    dosage=item.get("dosage"),
                    dose=item.get("dose"),
                    unit=item.get("unit"),
                    packaging=item.get("packaging"),
                    laboratory=item.get("laboratory"),
                    country=item.get("country"),
                    price=item.get("price"),
                    reimbursement=item.get("reimbursement"),
                    is_dental=item.get("is_dental", False),
                    requires_prescription=item.get("requires_prescription", True),
                    is_active=True,
                )
            )
        db.add_all(items_to_add)
        await db.flush()
        seeded += len(items_to_add)

    return {"seeded": seeded, "total": seeded}
