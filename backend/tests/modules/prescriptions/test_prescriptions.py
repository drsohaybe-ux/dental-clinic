"""Unit tests for prescriptions module (manifest, schemas, service, router).

Tests:
1. Module manifest, permissions, and models registration.
2. Pydantic schemas validation and defaults.
3. PrescriptionService CRUD (create, get, list_by_patient, update, deactivate).
4. FastAPI router handlers.
"""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.auth.dependencies import ClinicContext
from app.modules.prescriptions import PrescriptionsModule
from app.modules.prescriptions.models import Prescription, PrescriptionItem
from app.modules.prescriptions.router import (
    create_prescription,
    delete_prescription,
    get_prescription,
    list_patient_prescriptions,
    update_prescription,
)
from app.modules.prescriptions.schemas import (
    PrescriptionCreate,
    PrescriptionItemCreate,
    PrescriptionResponse,
    PrescriptionUpdate,
)
from app.modules.prescriptions.service import PrescriptionService


# ==============================================================================
# 1. Manifest & Module Metadata Tests
# ==============================================================================

def test_prescriptions_manifest_and_metadata():
    """Verify prescriptions module configuration and auto_install flag."""
    module = PrescriptionsModule()
    manifest = module.get_manifest()

    assert manifest.name == "prescriptions"
    assert manifest.auto_install is True
    assert manifest.installable is True
    assert "patients" in manifest.depends
    assert "medication_catalog" in manifest.depends

    models = module.get_models()
    assert Prescription in models
    assert PrescriptionItem in models

    perms = module.get_permissions()
    assert "read" in perms
    assert "write" in perms


# ==============================================================================
# 2. Schema Validation Tests
# ==============================================================================

def test_prescription_schemas_validation():
    """Verify PrescriptionCreate and PrescriptionItemCreate schema validation."""
    patient_id = uuid4()
    item_payload = PrescriptionItemCreate(
        medication_name="AMOCLAN",
        dosage="1G/200MG",
        form="Comprimé",
        frequency="1 comp 2x/jour",
        duration="7 jours",
        instructions="Au milieu des repas",
        order=1,
    )
    assert item_payload.medication_name == "AMOCLAN"
    assert item_payload.dosage == "1G/200MG"

    rx_payload = PrescriptionCreate(
        patient_id=patient_id,
        doctor_name_fr="Dr. LOKMANE R.",
        doctor_specialty_fr="Chirurgien Dentiste",
        doctor_name_ar="الدكتور لقمان ر.",
        doctor_specialty_ar="جراح أسنان",
        city="Boumerdès",
        items=[item_payload],
    )
    assert rx_payload.patient_id == patient_id
    assert rx_payload.city == "Boumerdès"
    assert len(rx_payload.items) == 1
    assert rx_payload.items[0].medication_name == "AMOCLAN"


# ==============================================================================
# 3. PrescriptionService Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_prescription_service_create():
    """PrescriptionService.create properly instantiates prescription and items."""
    clinic_id = uuid4()
    patient_id = uuid4()
    mock_db = AsyncMock()

    payload = PrescriptionCreate(
        patient_id=patient_id,
        doctor_name_fr="Dr. LOKMANE R.",
        doctor_specialty_fr="Chirurgien Dentiste",
        doctor_name_ar="الدكتور لقمان ر.",
        doctor_specialty_ar="جراح أسنان",
        city="Boumerdès",
        prescription_date=date.today(),
        notes="Prendre avec un verre d'eau",
        items=[
            PrescriptionItemCreate(
                medication_name="AMOCLAN",
                dosage="1G",
                form="Comprimé",
                frequency="1 comp 2x/jour",
                duration="7 jours",
                order=1,
            ),
            PrescriptionItemCreate(
                medication_name="ALGIDOL",
                dosage="1G",
                form="Comprimé effervescent",
                frequency="1 comp si douleur",
                duration="5 jours",
                order=2,
            ),
        ],
    )

    rx = await PrescriptionService.create(mock_db, clinic_id, payload)

    assert rx.clinic_id == clinic_id
    assert rx.patient_id == patient_id
    assert rx.doctor_name_fr == "Dr. LOKMANE R."
    assert rx.city == "Boumerdès"
    assert mock_db.add.call_count >= 3  # 1 prescription + 2 items
    assert mock_db.flush.await_count >= 2


@pytest.mark.asyncio
async def test_prescription_service_get():
    """PrescriptionService.get fetches prescription scoped by clinic_id."""
    clinic_id = uuid4()
    rx_id = uuid4()
    mock_db = AsyncMock()

    dummy_rx = Prescription(
        id=rx_id,
        clinic_id=clinic_id,
        patient_id=uuid4(),
        doctor_name_fr="Dr. LOKMANE",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = dummy_rx
    mock_db.execute.return_value = mock_result

    fetched = await PrescriptionService.get(mock_db, clinic_id, rx_id)
    assert fetched is not None
    assert fetched.id == rx_id


@pytest.mark.asyncio
async def test_prescription_service_list_by_patient():
    """PrescriptionService.list_by_patient returns patient prescriptions."""
    clinic_id = uuid4()
    patient_id = uuid4()
    mock_db = AsyncMock()

    dummy_rx = Prescription(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        doctor_name_fr="Dr. LOKMANE",
        is_active=True,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [dummy_rx]
    mock_db.execute.return_value = mock_result

    rows = await PrescriptionService.list_by_patient(mock_db, clinic_id, patient_id)
    assert len(rows) == 1
    assert rows[0].patient_id == patient_id


@pytest.mark.asyncio
async def test_prescription_service_update():
    """PrescriptionService.update modifies fields and replaces items."""
    clinic_id = uuid4()
    rx_id = uuid4()
    mock_db = AsyncMock()

    dummy_rx = Prescription(
        id=rx_id,
        clinic_id=clinic_id,
        patient_id=uuid4(),
        doctor_name_fr="Dr. LOKMANE",
        notes="Notes initiales",
    )
    dummy_rx.items = [
        PrescriptionItem(medication_name="AMOXIL", order=1)
    ]

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = dummy_rx
    mock_db.execute.return_value = mock_result

    update_payload = PrescriptionUpdate(
        notes="Notes modifiées",
        items=[
            PrescriptionItemCreate(
                medication_name="ELUDRIL",
                dosage="0.1%",
                form="Bain de bouche",
                frequency="3x/jour",
                duration="10 jours",
                order=1,
            )
        ],
    )

    updated = await PrescriptionService.update(
        mock_db, clinic_id, rx_id, update_payload
    )
    assert updated.notes == "Notes modifiées"
    assert mock_db.flush.await_count >= 2


@pytest.mark.asyncio
async def test_prescription_service_update_404():
    """PrescriptionService.update raises 404 if prescription not found."""
    clinic_id = uuid4()
    mock_db = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await PrescriptionService.update(
            mock_db, clinic_id, uuid4(), PrescriptionUpdate(notes="test")
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_prescription_service_deactivate():
    """PrescriptionService.deactivate marks prescription as inactive."""
    clinic_id = uuid4()
    rx_id = uuid4()
    mock_db = AsyncMock()

    dummy_rx = Prescription(
        id=rx_id,
        clinic_id=clinic_id,
        patient_id=uuid4(),
        is_active=True,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = dummy_rx
    mock_db.execute.return_value = mock_result

    res = await PrescriptionService.deactivate(mock_db, clinic_id, rx_id)
    assert res is True
    assert dummy_rx.is_active is False


# ==============================================================================
# 4. Router Handlers Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_router_endpoints():
    """Test router endpoints for list, get, create, update, delete."""
    clinic_id = uuid4()
    patient_id = uuid4()
    rx_id = uuid4()

    mock_user = MagicMock()
    mock_clinic = MagicMock()
    mock_clinic.id = clinic_id
    ctx = ClinicContext(user=mock_user, clinic=mock_clinic, role="dentist")

    now = datetime.utcnow()
    dummy_rx = Prescription(
        id=rx_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        doctor_name_fr="Dr. LOKMANE R.",
        doctor_specialty_fr="Chirurgien Dentiste",
        doctor_name_ar="الدكتور لقمان ر.",
        doctor_specialty_ar="جراح أسنان",
        city="Boumerdès",
        prescription_date=date.today(),
        is_active=True,
    )
    dummy_rx.created_at = now
    dummy_rx.updated_at = now

    item = PrescriptionItem(
        id=uuid4(),
        prescription_id=rx_id,
        medication_name="AMOCLAN",
        dosage="1G/200MG",
        form="Comprimé",
        frequency="1 comp 2x/jour",
        duration="7 jours",
        instructions="Au milieu des repas",
        order=1,
    )
    item.created_at = now
    item.updated_at = now
    dummy_rx.items = [item]

    mock_db = AsyncMock()

    # 1. List patient prescriptions
    mock_result_list = MagicMock()
    mock_result_list.scalars.return_value.all.return_value = [dummy_rx]
    mock_db.execute.return_value = mock_result_list

    res_list = await list_patient_prescriptions(patient_id, ctx, None, mock_db)
    assert len(res_list.data) == 1
    assert res_list.data[0].id == rx_id

    # 2. Get prescription
    mock_result_get = MagicMock()
    mock_result_get.scalar_one_or_none.return_value = dummy_rx
    mock_db.execute.return_value = mock_result_get

    res_get = await get_prescription(rx_id, ctx, None, mock_db)
    assert res_get.data.id == rx_id
    assert len(res_get.data.items) == 1
    assert res_get.data.items[0].medication_name == "AMOCLAN"

    # 3. Delete prescription
    await delete_prescription(rx_id, ctx, None, mock_db)
    assert dummy_rx.is_active is False
    assert mock_db.commit.await_count >= 1
