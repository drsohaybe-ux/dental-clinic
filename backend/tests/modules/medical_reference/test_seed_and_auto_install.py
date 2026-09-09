"""Unit tests for medical_reference seed data, module manifest, and auto-install."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.medical_reference import MedicalReferenceModule
from app.modules.medical_reference.seed import (
    DEFAULT_ALLERGIES,
    DEFAULT_DISEASES,
    DEFAULT_SURGERIES,
    seed_medical_reference,
)


def test_medical_reference_manifest_auto_install():
    """Verify medical_reference module is configured with auto_install=True."""
    module = MedicalReferenceModule()
    manifest = module.get_manifest()
    assert manifest.auto_install is True
    assert manifest.installable is True
    assert "patients_clinical" in manifest.depends


def test_seed_lists_comprehensive_coverage():
    """Verify default lists contain required dental/medical items."""
    # Allergies
    assert "Pénicilline" in DEFAULT_ALLERGIES
    assert "Amoxicilline" in DEFAULT_ALLERGIES
    assert "Aspirine" in DEFAULT_ALLERGIES
    assert "Latex" in DEFAULT_ALLERGIES
    assert "Iode" in DEFAULT_ALLERGIES
    assert any("Articaïne" in a or "Lidocaïne" in a for a in DEFAULT_ALLERGIES)

    # Systemic diseases
    assert "Diabète Type 1" in DEFAULT_DISEASES
    assert "Diabète Type 2" in DEFAULT_DISEASES
    assert any("Hypertension" in d for d in DEFAULT_DISEASES)
    assert any("Asthme" in d for d in DEFAULT_DISEASES)
    assert any("anticoagulant" in d.lower() for d in DEFAULT_DISEASES)
    assert any("bisphosphonate" in d.lower() for d in DEFAULT_DISEASES)

    # Surgeries
    assert "Extraction dentaire chirurgicale" in DEFAULT_SURGERIES
    assert "Pose d'implants dentaires" in DEFAULT_SURGERIES
    assert "Chirurgie cardiaque" in DEFAULT_SURGERIES
    assert "Greffe osseuse" in DEFAULT_SURGERIES


@pytest.mark.asyncio
async def test_seed_medical_reference_idempotent():
    """Verify seeder queries and adds missing items without duplicating existing ones."""
    clinic_id = uuid4()
    mock_db = AsyncMock()

    # First call: no existing entries
    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result_empty

    summary = await seed_medical_reference(mock_db, clinic_id)
    assert summary["allergies"] == len(DEFAULT_ALLERGIES)
    assert summary["diseases"] == len(DEFAULT_DISEASES)
    assert summary["surgeries"] == len(DEFAULT_SURGERIES)

    # Second call: all entries already exist
    mock_db.reset_mock()
    mock_result_full = MagicMock()
    mock_result_full.scalars.return_value.all.return_value = [
        name.lower() for name in DEFAULT_ALLERGIES + DEFAULT_DISEASES + DEFAULT_SURGERIES
    ]
    mock_db.execute.return_value = mock_result_full

    summary_second = await seed_medical_reference(mock_db, clinic_id)
    assert summary_second["allergies"] == 0
    assert summary_second["diseases"] == 0
    assert summary_second["surgeries"] == 0
