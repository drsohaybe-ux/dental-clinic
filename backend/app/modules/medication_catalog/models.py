"""medication_catalog — clinic-wide medication list (Settings → Clinical).

One row per medication available to the clinic: name, dose, unit,
pharmaceutical form and prescribable/active status. Seeded with a
56-item dental medication list via an idempotent seeder (runs on
``clinic.created`` and on demand through ``POST /medication_catalog/seed``).

Standalone module: `depends: []`. It is the data source for the
document-generation module (prescriptions), which reads it cross-module
under ADR 0002.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, Index, String, column, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin

# Pharmaceutical forms supported by the UI dropdown. Free-form names are
# deliberately NOT allowed — prescriptions (document generation) render
# these verbatim on the Rx layout.
MEDICATION_FORMS = (
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
)


class MedicationCatalogItem(Base, TimestampMixin):
    """A clinic-wide medication entry.

    ``name`` is unique per clinic at the DB level — case-insensitively,
    so 'Amoxicillin' and 'amoxicillin' cannot coexist (the same
    guarantee the service layer enforces with a 409; the functional
    index closes the concurrent-create race at the database, per the
    inventory #153 lesson about guarding invariants in SQL, not app code).
    """

    __tablename__ = "medication_catalog_items"
    __table_args__ = (
        # Case-insensitive uniqueness of (clinic, name) — declared here so
        # create_all-based tests exercise the same guard the migration
        # creates (mc_0001). clinic_id MUST be part of it: names are unique
        # per clinic, not globally. A plain UniqueConstraint would be
        # case-sensitive and leave the concurrent-create race open.
        Index(
            "uq_medication_catalog_clinic_name_ci",
            "clinic_id",
            func.lower(func.btrim(column("name", String))),
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    name: Mapped[str] = mapped_column(String(150))
    dose: Mapped[str | None] = mapped_column(String(50))
    unit: Mapped[str | None] = mapped_column(String(20))
    form: Mapped[str] = mapped_column(String(20), default="tablet")

    # Prescribed/active status pair: whether it needs an Rx, and whether
    # the clinic still stocks/uses it (inactive items stay for history).
    requires_prescription: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AlgerianMedication(Base, TimestampMixin):
    """Algerian National Medication Nomenclature (Nomenclature Nationale des Médicaments).

    Shared reference dataset (~4,636 items) containing all medications registered
    with the Algerian Ministry of Health (DCI, brand name, dosage, pharmaceutical form,
    registration number, laboratory, and dental tagging).
    """

    __tablename__ = "algerian_medications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    brand_name: Mapped[str] = mapped_column(String(200), index=True)
    dci: Mapped[str] = mapped_column(String(250), index=True)
    form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    standard_form: Mapped[str] = mapped_column(String(50), default="tablet")
    dosage: Mapped[str | None] = mapped_column(String(350), nullable=True)
    dose: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    packaging: Mapped[str | None] = mapped_column(String(500), nullable=True)
    laboratory: Mapped[str | None] = mapped_column(String(200), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[str | None] = mapped_column(String(150), nullable=True)
    reimbursement: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_dental: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    requires_prescription: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

