"""PrescriptionService — CRUD business logic for prescriptions and items."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Prescription, PrescriptionItem
from .schemas import PrescriptionCreate, PrescriptionUpdate


def _clean_str(val: object | None) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


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
            doctor_name_fr=_clean_str(payload.doctor_name_fr) or "Dr. Chirurgien Dentiste",
            doctor_specialty_fr=_clean_str(payload.doctor_specialty_fr) or "Chirurgien Dentiste",
            doctor_name_ar=_clean_str(payload.doctor_name_ar) or "الدكتور جراح أسنان",
            doctor_specialty_ar=_clean_str(payload.doctor_specialty_ar) or "جراح أسنان",
            city=_clean_str(payload.city) or "Alger",
            prescription_date=payload.prescription_date,
            notes=_clean_str(payload.notes),
            is_active=True,
        )
        db.add(prescription)
        await db.flush()

        for idx, item_data in enumerate(payload.items, start=1):
            item = PrescriptionItem(
                prescription=prescription,
                medication_name=_clean_str(item_data.medication_name) or "",
                dosage=_clean_str(item_data.dosage),
                form=_clean_str(item_data.form),
                frequency=_clean_str(item_data.frequency),
                duration=_clean_str(item_data.duration),
                instructions=_clean_str(item_data.instructions),
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
            if isinstance(value, str):
                setattr(prescription, key, _clean_str(value))
            else:
                setattr(prescription, key, value)

        if items_data is not None:
            # Replace existing items with updated items
            prescription.items.clear()
            await db.flush()

            for idx, item_data in enumerate(items_data, start=1):
                if isinstance(item_data, dict):
                    med_name = _clean_str(item_data.get("medication_name")) or ""
                    dosage = _clean_str(item_data.get("dosage"))
                    form = _clean_str(item_data.get("form"))
                    frequency = _clean_str(item_data.get("frequency"))
                    duration = _clean_str(item_data.get("duration"))
                    instructions = _clean_str(item_data.get("instructions"))
                    order_val = item_data.get("order")
                else:
                    med_name = _clean_str(getattr(item_data, "medication_name", "")) or ""
                    dosage = _clean_str(getattr(item_data, "dosage", None))
                    form = _clean_str(getattr(item_data, "form", None))
                    frequency = _clean_str(getattr(item_data, "frequency", None))
                    duration = _clean_str(getattr(item_data, "duration", None))
                    instructions = _clean_str(getattr(item_data, "instructions", None))
                    order_val = getattr(item_data, "order", None)

                item = PrescriptionItem(
                    prescription=prescription,
                    medication_name=med_name,
                    dosage=dosage,
                    form=form,
                    frequency=frequency,
                    duration=duration,
                    instructions=instructions,
                    order=order_val if order_val else idx,
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
