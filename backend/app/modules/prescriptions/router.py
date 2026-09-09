"""HTTP API endpoints for prescriptions module."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse
from app.database import get_db

from .schemas import PrescriptionCreate, PrescriptionResponse, PrescriptionUpdate
from .service import PrescriptionService

router = APIRouter()


@router.get("/patient/{patient_id}", response_model=ApiResponse[list[PrescriptionResponse]])
async def list_patient_prescriptions(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("prescriptions.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[PrescriptionResponse]]:
    """List all prescriptions for a patient."""
    items = await PrescriptionService.list_by_patient(db, ctx.clinic_id, patient_id)
    return ApiResponse(data=[PrescriptionResponse.model_validate(p) for p in items])


@router.get("/{prescription_id}", response_model=ApiResponse[PrescriptionResponse])
async def get_prescription(
    prescription_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("prescriptions.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PrescriptionResponse]:
    """Get a prescription by its ID."""
    prescription = await PrescriptionService.get(db, ctx.clinic_id, prescription_id)
    if prescription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )
    return ApiResponse(data=PrescriptionResponse.model_validate(prescription))


@router.post("", response_model=ApiResponse[PrescriptionResponse], status_code=status.HTTP_201_CREATED)
async def create_prescription(
    payload: PrescriptionCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("prescriptions.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PrescriptionResponse]:
    """Create a new prescription."""
    prescription = await PrescriptionService.create(db, ctx.clinic_id, payload)
    await db.commit()
    return ApiResponse(data=PrescriptionResponse.model_validate(prescription))


@router.put("/{prescription_id}", response_model=ApiResponse[PrescriptionResponse])
async def update_prescription(
    prescription_id: UUID,
    payload: PrescriptionUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("prescriptions.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PrescriptionResponse]:
    """Update an existing prescription."""
    prescription = await PrescriptionService.update(db, ctx.clinic_id, prescription_id, payload)
    await db.commit()
    return ApiResponse(data=PrescriptionResponse.model_validate(prescription))


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription(
    prescription_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("prescriptions.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft-delete a prescription."""
    await PrescriptionService.deactivate(db, ctx.clinic_id, prescription_id)
    await db.commit()
