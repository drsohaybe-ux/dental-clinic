"""PrescriptionService — CRUD business logic for prescriptions and items."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Prescription, PrescriptionItem
from .schemas import PrescriptionCreate, PrescriptionUpdate


class PrescriptionService:
    @staticmethod
    async def list_by_patient(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        active_only: bool = True,
    ) -> list[Prescription]:
        """List all prescriptions for a specific patient in reverse chronological order."""
        stmt = (
            select(Prescription)
            .where(
                Prescription.clinic_id == clinic_id,
                Prescription.patient_id == patient_id,
            )
            .options(selectinload(Prescription.items))
            .order_by(Prescription.prescription_date.desc(), Prescription.created_at.desc())
        )
        if active_only:
            stmt = stmt.where(Prescription.is_active.is_(True))

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get(
        db: AsyncSession,
        clinic_id: UUID,
        prescription_id: UUID,
    ) -> Prescription | None:
        """Fetch a single prescription with items loaded."""
        stmt = (
            select(Prescription)
            .where(
                Prescription.id == prescription_id,
                Prescription.clinic_id == clinic_id,
            )
            .options(selectinload(Prescription.items))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        clinic_id: UUID,
        payload: PrescriptionCreate,
    ) -> Prescription:
        """Create a new prescription with its prescribed medication items."""
        prescription = Prescription(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            doctor_name_fr=payload.doctor_name_fr,
            doctor_specialty_fr=payload.doctor_specialty_fr,
            doctor_name_ar=payload.doctor_name_ar,
            doctor_specialty_ar=payload.doctor_specialty_ar,
            city=payload.city,
            prescription_date=payload.prescription_date,
            notes=payload.notes,
            is_active=True,
        )
        db.add(prescription)
        await db.flush()

        for idx, item_data in enumerate(payload.items, start=1):
            item = PrescriptionItem(
                prescription_id=prescription.id,
                medication_name=item_data.medication_name.strip(),
                dosage=item_data.dosage.strip() if item_data.dosage else None,
                form=item_data.form.strip() if item_data.form else None,
                frequency=item_data.frequency.strip() if item_data.frequency else None,
                duration=item_data.duration.strip() if item_data.duration else None,
                instructions=item_data.instructions.strip() if item_data.instructions else None,
                order=item_data.order if item_data.order else idx,
            )
            db.add(item)

        await db.flush()
        await db.refresh(prescription, attribute_names=["items"])
        return prescription

    @staticmethod
    async def update(
        db: AsyncSession,
        clinic_id: UUID,
        prescription_id: UUID,
        payload: PrescriptionUpdate,
    ) -> Prescription:
        """Update an existing prescription and optionally replace its items."""
        prescription = await PrescriptionService.get(db, clinic_id, prescription_id)
        if prescription is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        items_data = update_data.pop("items", None)

        for key, value in update_data.items():
            setattr(prescription, key, value)

        if items_data is not None:
            # Replace existing items with updated items
            prescription.items.clear()
            await db.flush()

            for idx, item_data in enumerate(items_data, start=1):
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medication_name=item_data["medication_name"].strip(),
                    dosage=item_data.get("dosage", "").strip() or None,
                    form=item_data.get("form", "").strip() or None,
                    frequency=item_data.get("frequency", "").strip() or None,
                    duration=item_data.get("duration", "").strip() or None,
                    instructions=item_data.get("instructions", "").strip() or None,
                    order=item_data.get("order", idx),
                )
                db.add(item)

        await db.flush()
        await db.refresh(prescription, attribute_names=["items"])
        return prescription

    @staticmethod
    async def deactivate(
        db: AsyncSession,
        clinic_id: UUID,
        prescription_id: UUID,
    ) -> bool:
        """Soft delete a prescription."""
        prescription = await PrescriptionService.get(db, clinic_id, prescription_id)
        if prescription is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )
        prescription.is_active = False
        await db.flush()
        return True
