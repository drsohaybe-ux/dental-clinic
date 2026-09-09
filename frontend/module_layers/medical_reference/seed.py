"""Seed data for medical_reference module.

Comprehensive dental/medical starter lists for:
- ReferenceAllergy: Common drug, material, and environmental allergies
- ReferenceDisease: Systemic diseases critical for dental/medical treatment
- ReferenceSurgery: Common surgical history procedures

Idempotent: skips entries that already exist for the clinic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select

from .models import ReferenceAllergy, ReferenceDisease, ReferenceSurgery

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


DEFAULT_ALLERGIES: list[str] = [
    "Pénicilline",
    "Amoxicilline",
    "Aspirine",
    "AINS (Ibuprofène, Kétoprofène)",
    "Sulfamides",
    "Codéine",
    "Articaïne",
    "Lidocaïne",
    "Érythromycine",
    "Latex",
    "Iode",
    "Paracétamol",
    "Céphalosporines",
    "Tétracyclines",
    "Clindamycine",
    "Anesthésiques locaux (amides)",
    "Produits de contraste iodés",
]

DEFAULT_DISEASES: list[str] = [
    "Diabète Type 1",
    "Diabète Type 2",
    "Hypertension artérielle (HTA)",
    "Asthme",
    "Valvulopathie / Risque endocardite",
    "Insuffisance rénale chronique",
    "Sous anticoagulants (Sintrom, Plavix, Eliquis)",
    "Sous Bisphosphonates (Aclasta, Fosamax - risque ostéonécrose)",
    "Épilepsie",
    "Hépatite B",
    "Hépatite C",
    "Grossesse",
    "Allaitement",
    "Cardiopathie ischémique (Infarctus / Angor)",
    "Porteur de Pacemaker",
    "Insuffisance cardiaque",
    "VIH / Immunodépression",
    "Troubles de la coagulation (Hémophilie)",
    "Insuffisance hépatique",
    "Cancer sous chimiothérapie / radiothérapie",
]

DEFAULT_SURGERIES: list[str] = [
    "Extraction dentaire chirurgicale",
    "Pose d'implants dentaires",
    "Chirurgie cardiaque",
    "Césarienne",
    "Appendicectomie",
    "Greffe osseuse",
    "Avulsion de dents de sagesse incluses",
    "Comblement de sinus (Sinus Lift)",
    "Chirurgie parodontale",
    "Frénectomie",
    "Résection apicale",
    "Chirurgie orthognathique",
    "Cholécystectomie",
    "Pontage aorto-coronarien",
    "Pose de prothèse de hanche / genou",
]


async def seed_medical_reference(db: AsyncSession, clinic_id: UUID) -> dict[str, int]:
    """Idempotently seed default allergies, diseases, and surgeries for a clinic."""
    inserted = {"allergies": 0, "diseases": 0, "surgeries": 0}

    # 1. Allergies
    existing_allergies_stmt = select(func.lower(ReferenceAllergy.name)).where(
        ReferenceAllergy.clinic_id == clinic_id
    )
    existing_allergies = set((await db.execute(existing_allergies_stmt)).scalars().all())
    for name in DEFAULT_ALLERGIES:
        if name.lower() not in existing_allergies:
            db.add(ReferenceAllergy(clinic_id=clinic_id, name=name, is_active=True))
            existing_allergies.add(name.lower())
            inserted["allergies"] += 1

    # 2. Systemic diseases
    existing_diseases_stmt = select(func.lower(ReferenceDisease.name)).where(
        ReferenceDisease.clinic_id == clinic_id
    )
    existing_diseases = set((await db.execute(existing_diseases_stmt)).scalars().all())
    for name in DEFAULT_DISEASES:
        if name.lower() not in existing_diseases:
            db.add(ReferenceDisease(clinic_id=clinic_id, name=name, is_active=True))
            existing_diseases.add(name.lower())
            inserted["diseases"] += 1

    # 3. Surgeries
    existing_surgeries_stmt = select(func.lower(ReferenceSurgery.name)).where(
        ReferenceSurgery.clinic_id == clinic_id
    )
    existing_surgeries = set((await db.execute(existing_surgeries_stmt)).scalars().all())
    for name in DEFAULT_SURGERIES:
        if name.lower() not in existing_surgeries:
            db.add(ReferenceSurgery(clinic_id=clinic_id, name=name, is_active=True))
            existing_surgeries.add(name.lower())
            inserted["surgeries"] += 1

    if any(inserted.values()):
        await db.flush()

    return inserted
