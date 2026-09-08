"""MedicationCatalogService — clinic-scoped CRUD over the medication list.

Every query filters on ``clinic_id``. Duplicate names are rejected
case-insensitively with a 409 (create and rename), mirroring the
medical_reference behaviour; the DB-level unique constraint closes the
concurrent-create race.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AlgerianMedication, MedicationCatalogItem
from .schemas import (
    MedicationCatalogCreate,
    MedicationCatalogUpdate,
    QuickAddMedicationPayload,
)



def _norm(name: str) -> str:
    """Must match the DB index key exactly (``lower(btrim(name))``).

    Collapsing inner whitespace here too would make the app check *looser*
    than the index: "Ibuprofen  400 mg" typed twice passes the 409 lookup
    and then trips the unique index as a raw 500.
    """
    return name.strip().lower()


class MedicationCatalogService:
    @staticmethod
    async def list_items(
        db: AsyncSession,
        clinic_id: UUID,
        q: str | None = None,
        form: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[MedicationCatalogItem], int]:
        stmt = select(MedicationCatalogItem).where(MedicationCatalogItem.clinic_id == clinic_id)
        if q:
            stmt = stmt.where(MedicationCatalogItem.name.ilike(f"%{q}%"))
        if form:
            stmt = stmt.where(MedicationCatalogItem.form == form)
        if is_active is not None:
            stmt = stmt.where(MedicationCatalogItem.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(MedicationCatalogItem.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total

    @staticmethod
    async def get_item(db: AsyncSession, clinic_id: UUID, item_id: UUID) -> MedicationCatalogItem:
        stmt = select(MedicationCatalogItem).where(
            MedicationCatalogItem.id == item_id,
            MedicationCatalogItem.clinic_id == clinic_id,
        )
        item = (await db.execute(stmt)).scalar_one_or_none()
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found"
            )
        return item

    @staticmethod
    async def find_by_name(
        db: AsyncSession, clinic_id: UUID, name: str
    ) -> MedicationCatalogItem | None:
        """Case-insensitive lookup used by create/update and the seeder."""
        stmt = select(MedicationCatalogItem).where(
            MedicationCatalogItem.clinic_id == clinic_id,
            func.lower(func.btrim(MedicationCatalogItem.name)) == _norm(name),
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create_item(
        db: AsyncSession, clinic_id: UUID, payload: MedicationCatalogCreate
    ) -> MedicationCatalogItem:
        existing = await MedicationCatalogService.find_by_name(db, clinic_id, payload.name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A medication with this name already exists",
            )
        item = MedicationCatalogItem(clinic_id=clinic_id, **payload.model_dump())
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def update_item(
        db: AsyncSession, clinic_id: UUID, item_id: UUID, payload: MedicationCatalogUpdate
    ) -> MedicationCatalogItem:
        item = await MedicationCatalogService.get_item(db, clinic_id, item_id)
        data = payload.model_dump(exclude_unset=True)

        new_name = data.get("name")
        if new_name is not None and _norm(new_name) != _norm(item.name):
            other = await MedicationCatalogService.find_by_name(db, clinic_id, new_name)
            if other is not None and other.id != item.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A medication with this name already exists",
                )

        for field, value in data.items():
            setattr(item, field, value)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_item(db: AsyncSession, clinic_id: UUID, item_id: UUID) -> None:
        item = await MedicationCatalogService.get_item(db, clinic_id, item_id)
        await db.delete(item)
        await db.commit()

    @staticmethod
    async def search_nomenclature(
        db: AsyncSession,
        q: str | None = None,
        is_dental: bool | None = None,
        limit: int = 30,
    ) -> list[AlgerianMedication]:
        """Search Algerian National Nomenclature.

        Supports case-insensitive partial match on brand_name or dci.
        Prioritizes exact/prefix brand matches and dental medications.
        Falls back to local cached dataset if table has not yet been seeded.
        """
        limit = min(max(1, limit), 100)
        try:
            stmt = select(AlgerianMedication).where(AlgerianMedication.is_active.is_(True))
            if is_dental is not None:
                stmt = stmt.where(AlgerianMedication.is_dental == is_dental)
            if q:
                query_norm = q.strip().lower()
                stmt = stmt.where(
                    or_(
                        func.lower(AlgerianMedication.brand_name).contains(query_norm),
                        func.lower(AlgerianMedication.dci).contains(query_norm),
                    )
                )
                stmt = stmt.order_by(
                    func.lower(AlgerianMedication.brand_name).startswith(query_norm).desc(),
                    AlgerianMedication.is_dental.desc(),
                    AlgerianMedication.brand_name.asc(),
                )
            else:
                stmt = stmt.order_by(
                    AlgerianMedication.is_dental.desc(),
                    AlgerianMedication.brand_name.asc(),
                )
            stmt = stmt.limit(limit)
            rows = list((await db.execute(stmt)).scalars().all())
            if rows:
                return rows
        except Exception:
            pass

        from .seed_algeria import load_nomenclature_records

        try:
            records = load_nomenclature_records()
        except Exception:
            return []

        q_norm = q.strip().lower() if q else ""
        filtered = []
        for r in records:
            if is_dental is not None and r.get("is_dental") != is_dental:
                continue
            brand = (r.get("brand_name") or "").lower()
            dci = (r.get("dci") or "").lower()
            if q_norm and (q_norm not in brand and q_norm not in dci):
                continue
            filtered.append(r)

        def sort_key(x):
            b = (x.get("brand_name") or "").lower()
            prefix_match = 0 if (q_norm and b.startswith(q_norm)) else 1
            dental_match = 0 if x.get("is_dental") else 1
            return (prefix_match, dental_match, b)

        filtered.sort(key=sort_key)
        top = filtered[:limit]

        result = []
        for item in top:
            result.append(
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
        return result

    @staticmethod
    async def quick_add_to_catalog(
        db: AsyncSession,
        clinic_id: UUID,
        payload: QuickAddMedicationPayload,
    ) -> tuple[MedicationCatalogItem, bool]:
        """Idempotently add a medication to the clinic's catalog.

        Returns (item, created).
        """
        existing = await MedicationCatalogService.find_by_name(db, clinic_id, payload.name)
        if existing is not None:
            return existing, False

        item = MedicationCatalogItem(
            clinic_id=clinic_id,
            name=payload.name.strip(),
            dose=payload.dose,
            unit=payload.unit,
            form=payload.form,
            requires_prescription=payload.requires_prescription,
            is_active=payload.is_active,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item, True

