"""Pydantic schemas for the prescriptions module."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionItemBase(BaseModel):
    medication_name: str = Field(..., min_length=1, max_length=200)
    dosage: str | None = Field(default=None, max_length=100)
    form: str | None = Field(default=None, max_length=100)
    frequency: str | None = Field(default=None, max_length=200)
    duration: str | None = Field(default=None, max_length=100)
    instructions: str | None = Field(default=None, max_length=500)
    order: int = 1


class PrescriptionItemCreate(PrescriptionItemBase):
    pass


class PrescriptionItemResponse(PrescriptionItemBase):
    id: UUID
    prescription_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PrescriptionBase(BaseModel):
    patient_id: UUID
    doctor_name_fr: str = Field(default="Dr. LOKMANE R.", max_length=150)
    doctor_specialty_fr: str = Field(default="Chirurgien Dentiste", max_length=150)
    doctor_name_ar: str = Field(default="الدكتور لقمان ر.", max_length=150)
    doctor_specialty_ar: str = Field(default="جراح أسنان", max_length=150)
    city: str = Field(default="Boumerdès", max_length=100)
    prescription_date: date = Field(default_factory=date.today)
    notes: str | None = None


class PrescriptionCreate(PrescriptionBase):
    items: list[PrescriptionItemCreate] = Field(default_factory=list)


class PrescriptionUpdate(BaseModel):
    doctor_name_fr: str | None = Field(default=None, max_length=150)
    doctor_specialty_fr: str | None = Field(default=None, max_length=150)
    doctor_name_ar: str | None = Field(default=None, max_length=150)
    doctor_specialty_ar: str | None = Field(default=None, max_length=150)
    city: str | None = Field(default=None, max_length=100)
    prescription_date: date | None = None
    notes: str | None = None
    items: list[PrescriptionItemCreate] | None = None


class PrescriptionResponse(PrescriptionBase):
    id: UUID
    clinic_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: list[PrescriptionItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
