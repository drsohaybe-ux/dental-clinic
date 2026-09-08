"""Pydantic schemas for the medication catalog."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import MEDICATION_FORMS

MedicationForm = Literal[
    "tablet",
    "capsule",
    "syrup",
    "suspension",
    "injection",
    "topical",
    "drops",
    "spray",
    "mouthwash",
    "gel",
    "cream",
    "paste",
    "varnish",
    "other",
]

assert set(MEDICATION_FORMS) == set(MedicationForm.__args__)  # keep in sync


class MedicationCatalogCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    dose: str | None = Field(default=None, max_length=50)
    unit: str | None = Field(default=None, max_length=20)
    form: MedicationForm = "tablet"
    requires_prescription: bool = True
    is_active: bool = True


class MedicationCatalogUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    dose: str | None = Field(default=None, max_length=50)
    unit: str | None = Field(default=None, max_length=20)
    form: MedicationForm | None = None
    requires_prescription: bool | None = None
    is_active: bool | None = None


class MedicationCatalogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    name: str
    dose: str | None
    unit: str | None
    form: str
    requires_prescription: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MedicationSeedSummary(BaseModel):
    created: int
    skipped: int


class AlgerianMedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str | None = None
    registration_number: str | None = None
    brand_name: str
    dci: str
    form: str | None = None
    standard_form: str = "tablet"
    dosage: str | None = None
    dose: str | None = None
    unit: str | None = None
    packaging: str | None = None
    laboratory: str | None = None
    country: str | None = None
    price: str | None = None
    reimbursement: str | None = None
    is_dental: bool = False
    requires_prescription: bool = True
    is_active: bool = True


class NomenclatureSeedSummary(BaseModel):
    seeded: int
    total: int


class QuickAddMedicationPayload(BaseModel):
    """Payload to add a medication to clinic catalog from nomenclature or on-the-fly."""

    name: str = Field(min_length=1, max_length=150)
    dose: str | None = Field(default=None, max_length=50)
    unit: str | None = Field(default=None, max_length=20)
    form: MedicationForm = "tablet"
    requires_prescription: bool = True
    is_active: bool = True

