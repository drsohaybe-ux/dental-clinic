"""prescriptions — Doctor prescription pad (Ordonnance) models.

Manages official medical prescriptions issued by dentists/doctors for patients.
Stores doctor metadata in French and Arabic, patient details, clinic location,
and an ordered list of prescribed medications with dosages, forms, posology,
and durations.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.patients.models import Patient


class Prescription(Base, TimestampMixin):
    """An official medical prescription ("Ordonnance") issued for a patient."""

    __tablename__ = "prescriptions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    patient_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Doctor and specialty in French (top-left on Algerian prescription pad)
    doctor_name_fr: Mapped[str] = mapped_column(String(150), default="Dr. LOKMANE R.")
    doctor_specialty_fr: Mapped[str] = mapped_column(String(150), default="Chirurgien Dentiste")

    # Doctor and specialty in Arabic (top-right on Algerian prescription pad)
    doctor_name_ar: Mapped[str] = mapped_column(String(150), default="الدكتور لقمان ر.")
    doctor_specialty_ar: Mapped[str] = mapped_column(String(150), default="جراح أسنان")

    # Date and city line (e.g. "Boumerdès, le: 09/09/2026")
    city: Mapped[str] = mapped_column(String(100), default="Boumerdès")
    prescription_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Clinical notes, instructions, or internal remarks
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft-delete flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Ordered items on this prescription
    items: Mapped[list[PrescriptionItem]] = relationship(
        "PrescriptionItem",
        back_populates="prescription",
        cascade="all, delete-orphan",
        order_by="PrescriptionItem.order",
    )

    patient: Mapped[Patient] = relationship("Patient")


class PrescriptionItem(Base, TimestampMixin):
    """An individual drug item on an Ordonnance with dosage, form, posology, and duration."""

    __tablename__ = "prescription_items"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    prescription_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    medication_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(200), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    instructions: Mapped[str | None] = mapped_column(String(500), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    prescription: Mapped[Prescription] = relationship("Prescription", back_populates="items")
