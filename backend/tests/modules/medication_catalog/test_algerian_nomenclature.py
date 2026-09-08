"""Unit tests for Algerian National Medication Nomenclature integration.

Verifies:
1. Nomenclature dataset cache integrity and complete coverage of required Algerian brands.
2. Search priority ranking (brand prefix matches first, dental prioritization).
3. Search filtering (dental-only flag, limit constraints, case insensitivity).
4. Graceful fallback to cached JSON when DB is empty or unseeded.
5. Idempotent quick-add to clinic catalog (handles duplicates gracefully).
6. Seeder batching and idempotency.
7. Model registration in MedicationCatalogModule.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.modules.medication_catalog import MedicationCatalogModule
from app.modules.medication_catalog.models import (
    MEDICATION_FORMS,
    AlgerianMedication,
    MedicationCatalogItem,
)
from app.modules.medication_catalog.schemas import (
    AlgerianMedicationResponse,
    NomenclatureSeedSummary,
    QuickAddMedicationPayload,
)
from app.modules.medication_catalog.seed_algeria import (
    load_nomenclature_records,
    seed_algerian_nomenclature,
)
from app.modules.medication_catalog.service import MedicationCatalogService

# Required trade brands confirmed by user
REQUIRED_ALGERIAN_BRANDS = [
    "Augmentin",
    "Amoxil",
    "Clamoxyl",
    "Birodogyl",
    "Rodogyl",
    "Doliprane",
    "Algidol",
    "Cataflam",
    "Hextril",
    "Eludril",
    "Solupred",
    "Septanest",
    "Alphacaine",
]


# ==============================================================================
# 1. Dataset Integrity and Brand Coverage Tests
# ==============================================================================

def test_nomenclature_dataset_loaded_and_valid():
    """Verify the cached nomenclature dataset loads with all records and valid schemas."""
    records = load_nomenclature_records()
    assert len(records) == 4636, f"Expected 4,636 records, got {len(records)}"

    dental_count = 0
    for r in records:
        assert "id" in r and r["id"], "Each record must have a unique ID"
        assert "brand_name" in r and r["brand_name"], "Record missing brand_name"
        assert "dci" in r and r["dci"], "Record missing dci"
        assert "standard_form" in r, "Record missing standard_form"
        assert r["standard_form"] in MEDICATION_FORMS, (
            f"Invalid standard_form '{r['standard_form']}' for {r['brand_name']}"
        )
        if r.get("is_dental"):
            dental_count += 1

    assert dental_count == 982, f"Expected 982 dental records, got {dental_count}"


def test_required_algerian_brands_presence_and_dental_tagging():
    """Verify that 100% of the user's requested Algerian trade brands are present and tagged dental."""
    records = load_nomenclature_records()

    for brand in REQUIRED_ALGERIAN_BRANDS:
        brand_lower = brand.lower()
        matches = [
            r for r in records
            if brand_lower in (r.get("brand_name") or "").lower()
        ]
        assert len(matches) > 0, f"Required brand '{brand}' was not found in nomenclature dataset"

        dental_matches = [m for m in matches if m.get("is_dental") is True]
        assert len(dental_matches) > 0, (
            f"Brand '{brand}' matches found ({len(matches)}), but none were tagged dental"
        )


# ==============================================================================
# 2. Search Ordering, Dental Priority, and Fallback Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_search_nomenclature_fallback_cache_without_query():
    """When DB is unavailable or empty, search_nomenclature gracefully uses cached JSON."""
    results = await MedicationCatalogService.search_nomenclature(None, q=None, limit=20)
    assert len(results) == 20
    assert all(isinstance(r, AlgerianMedication) for r in results)
    # Dental medications must be prioritized first
    first_dental = [r.is_dental for r in results[:10]]
    assert any(first_dental), "Dental medications should be prioritized at the top"


@pytest.mark.asyncio
async def test_search_nomenclature_prefix_and_dental_ranking():
    """Prefix matches on brand_name should rank first, with dental priority within."""
    results = await MedicationCatalogService.search_nomenclature(None, q="Augmentin", limit=10)
    assert len(results) > 0
    top = results[0]
    assert top.brand_name.upper().startswith("AUGMENTIN")
    assert top.is_dental is True


@pytest.mark.asyncio
async def test_search_nomenclature_anesthetics_and_mouthwashes():
    """Verify dental clinic specifics like Septanest, Alphacaine, and Eludril are found."""
    for product in ("Septanest", "Alphacaine", "Eludril", "Hextril"):
        res = await MedicationCatalogService.search_nomenclature(None, q=product, limit=5)
        assert len(res) > 0, f"Product {product} returned no search results"
        assert any(product.lower() in r.brand_name.lower() for r in res)
        assert res[0].is_dental is True


@pytest.mark.asyncio
async def test_search_nomenclature_dental_filter_flag():
    """is_dental parameter strictly limits results to dental or non-dental medications."""
    dental_only = await MedicationCatalogService.search_nomenclature(None, q="a", is_dental=True, limit=15)
    assert len(dental_only) > 0
    assert all(r.is_dental is True for r in dental_only)

    non_dental_only = await MedicationCatalogService.search_nomenclature(None, q="a", is_dental=False, limit=15)
    assert len(non_dental_only) > 0
    assert all(r.is_dental is False for r in non_dental_only)


@pytest.mark.asyncio
async def test_search_nomenclature_limit_clamp():
    """Limit is clamped between 1 and 100."""
    res_1 = await MedicationCatalogService.search_nomenclature(None, q=None, limit=1)
    assert len(res_1) == 1

    res_5 = await MedicationCatalogService.search_nomenclature(None, q=None, limit=5)
    assert len(res_5) == 5


# ==============================================================================
# 3. Quick-Add to Clinic Catalog Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_quick_add_creates_new_catalog_item():
    """quick_add_to_catalog creates a MedicationCatalogItem when not present."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    clinic_id = uuid4()

    # find_by_name returns None (not present)
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_execute_result

    payload = QuickAddMedicationPayload(
        name="Augmentin 1g/125mg",
        dose="1g/125mg",
        unit=None,
        form="tablet",
        requires_prescription=True,
    )

    item, created = await MedicationCatalogService.quick_add_to_catalog(mock_db, clinic_id, payload)
    assert created is True
    assert item.clinic_id == clinic_id
    assert item.name == "Augmentin 1g/125mg"
    assert item.form == "tablet"
    assert item.requires_prescription is True
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_quick_add_idempotent_on_existing_item():
    """quick_add_to_catalog returns existing item without duplicate error."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    clinic_id = uuid4()

    existing_item = MedicationCatalogItem(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Augmentin 1g/125mg",
        dose="1g/125mg",
        unit=None,
        form="tablet",
    )

    # find_by_name returns existing_item
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = existing_item
    mock_db.execute.return_value = mock_execute_result

    payload = QuickAddMedicationPayload(
        name="augmentin 1g/125mg",
        form="tablet",
    )

    item, created = await MedicationCatalogService.quick_add_to_catalog(mock_db, clinic_id, payload)
    assert created is False
    assert item == existing_item
    mock_db.add.assert_not_called()


# ==============================================================================
# 4. Seeder Logic & Idempotency Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_seed_algerian_nomenclature_skips_when_already_seeded():
    """If algerian_medications table already has rows, seed skips without re-inserting."""
    mock_db = AsyncMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 4636
    mock_db.execute.return_value = mock_count_result

    summary = await seed_algerian_nomenclature(mock_db, force_refresh=False)
    assert summary == {"seeded": 0, "total": 4636}
    mock_db.add_all.assert_not_called()


@pytest.mark.asyncio
async def test_seed_algerian_nomenclature_batches_records():
    """When table is empty or force=True, seed batches all records in chunks."""
    mock_db = AsyncMock()
    mock_db.add_all = MagicMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 0
    mock_db.execute.return_value = mock_count_result

    summary = await seed_algerian_nomenclature(mock_db, force_refresh=False)
    assert summary["seeded"] == 4636
    assert summary["total"] == 4636
    # 4,636 items in chunks of 500 = 10 chunks (10 add_all calls)
    assert mock_db.add_all.call_count == 10
    assert mock_db.flush.await_count == 10


# ==============================================================================
# 5. Schema Validation & Module Registration Tests
# ==============================================================================

def test_algerian_medication_response_schema():
    """AlgerianMedicationResponse schema correctly serializes model instances."""
    med_id = uuid4()
    med = AlgerianMedication(
        id=med_id,
        code="ALG001",
        registration_number="123/456",
        brand_name="AMOXIL",
        dci="Amoxicilline",
        form="Gélule",
        standard_form="capsule",
        dosage="500 mg",
        dose="500",
        unit="mg",
        packaging="Boite de 20",
        laboratory="GSK",
        country="Algeria",
        price="350 DZD",
        reimbursement="80%",
        is_dental=True,
        requires_prescription=True,
        is_active=True,
    )
    dto = AlgerianMedicationResponse.model_validate(med)
    assert dto.id == med_id
    assert dto.brand_name == "AMOXIL"
    assert dto.dci == "Amoxicilline"
    assert dto.standard_form == "capsule"
    assert dto.is_dental is True


def test_quick_add_payload_validation():
    """QuickAddMedicationPayload enforces valid medication forms."""
    valid = QuickAddMedicationPayload(name="Doliprane 1000mg", form="tablet")
    assert valid.form == "tablet"

    with pytest.raises(Exception):
        QuickAddMedicationPayload(name="Doliprane 1000mg", form="invalid_form_xyz")


def test_module_manifest_and_models():
    """MedicationCatalogModule properly declares AlgerianMedication in get_models()."""
    module = MedicationCatalogModule()
    models = module.get_models()
    model_names = [m.__name__ for m in models]
    assert "MedicationCatalogItem" in model_names
    assert "AlgerianMedication" in model_names


# ==============================================================================
# 6. HTTP Router Endpoint Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_router_search_nomenclature_endpoint():
    """Test GET /api/v1/medication_catalog/nomenclature router handler."""
    from app.core.auth.dependencies import ClinicContext
    from app.modules.medication_catalog.router import search_nomenclature as router_search

    mock_user = MagicMock()
    mock_clinic = MagicMock()
    mock_clinic.id = uuid4()
    ctx = ClinicContext(user=mock_user, clinic=mock_clinic, role="dentist")

    # Call endpoint with empty DB mock (fallback to cache)
    mock_db = AsyncMock()
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_execute_result

    response = await router_search(ctx=ctx, db=mock_db, q="Augmentin", is_dental=True, limit=5)
    assert response.data is not None
    assert len(response.data) > 0
    assert all(isinstance(r, AlgerianMedicationResponse) for r in response.data)
    assert response.data[0].brand_name.upper().startswith("AUGMENTIN")
    assert response.data[0].is_dental is True


@pytest.mark.asyncio
async def test_router_quick_add_endpoint():
    """Test POST /api/v1/medication_catalog/quick-add router handler."""
    from datetime import datetime, timezone
    from app.core.auth.dependencies import ClinicContext
    from app.modules.medication_catalog.router import quick_add_medication as router_quick_add

    clinic_id = uuid4()
    mock_user = MagicMock()
    mock_clinic = MagicMock()
    mock_clinic.id = clinic_id
    ctx = ClinicContext(user=mock_user, clinic=mock_clinic, role="dentist")

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    # Simulate new item
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_execute_result

    # Give the created item an ID and timestamps when refreshed
    async def fake_refresh(item):
        item.id = uuid4()
        item.created_at = datetime.now(timezone.utc)
        item.updated_at = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = fake_refresh

    payload = QuickAddMedicationPayload(
        name="Cataflam 50mg",
        dose="50",
        unit="mg",
        form="tablet",
    )

    response = await router_quick_add(payload=payload, ctx=ctx, _=None, db=mock_db)
    assert response.data is not None
    assert response.data.name == "Cataflam 50mg"
    assert response.data.form == "tablet"
    assert response.data.clinic_id == clinic_id


@pytest.mark.asyncio
async def test_router_seed_endpoint():
    """Test POST /api/v1/medication_catalog/nomenclature/seed router handler."""
    from app.core.auth.dependencies import ClinicContext
    from app.modules.medication_catalog.router import seed_nomenclature_endpoint

    mock_user = MagicMock()
    mock_clinic = MagicMock()
    mock_clinic.id = uuid4()
    ctx = ClinicContext(user=mock_user, clinic=mock_clinic, role="dentist")

    mock_db = AsyncMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 4636
    mock_db.execute.return_value = mock_count_result

    response = await seed_nomenclature_endpoint(ctx=ctx, _=None, db=mock_db, force=False)
    assert response.data is not None
    assert response.data.total == 4636
    assert response.data.seeded == 0
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_seeder_force_refresh_deletes_existing():
    """Verify that force_refresh=True deletes existing rows to prevent primary key collision."""
    mock_db = AsyncMock()
    mock_db.add_all = MagicMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 100
    mock_db.execute.return_value = mock_count_result

    summary = await seed_algerian_nomenclature(mock_db, force_refresh=True)
    assert summary["seeded"] == 4636
    assert summary["total"] == 4636
    # Verify execute was called at least twice (count + delete)
    assert mock_db.execute.await_count >= 2


def test_field_lengths_strictly_within_db_limits():
    """All 4,636 records must fit within the PostgreSQL column VARCHAR lengths."""
    records = load_nomenclature_records()
    for r in records:
        assert len(r.get("brand_name", "")) <= 200, f"brand_name too long: {r['brand_name']}"
        assert len(r.get("dci", "")) <= 250, f"dci too long: {r['dci']}"
        if r.get("dosage"):
            assert len(r["dosage"]) <= 350, f"dosage too long: {r['dosage']}"
        if r.get("dose"):
            assert len(r["dose"]) <= 50, f"dose too long: {r['dose']}"
        if r.get("unit"):
            assert len(r["unit"]) <= 20, f"unit too long: {r['unit']}"
        if r.get("packaging"):
            assert len(r["packaging"]) <= 500, f"packaging too long: {r['packaging']}"
        if r.get("laboratory"):
            assert len(r["laboratory"]) <= 200, f"laboratory too long: {r['laboratory']}"
        if r.get("price"):
            assert len(r["price"]) <= 150, f"price too long: {r['price']}"


@pytest.mark.asyncio
async def test_quick_add_clamps_overflowing_fields():
    """quick_add_to_catalog must safely clamp fields exceeding MedicationCatalogItem limits."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    clinic_id = uuid4()
    payload = QuickAddMedicationPayload(
        name="A" * 200,  # exceeds 150
        dose="1" * 80,   # exceeds 50
        unit="mg" * 20,  # exceeds 20
        form="tablet",
    )

    item, created = await MedicationCatalogService.quick_add_to_catalog(mock_db, clinic_id, payload)
    assert created is True
    assert len(item.name) <= 150
    assert len(item.dose) <= 50
    assert len(item.unit) <= 20


def test_role_permissions_grants_dentist_write():
    """Dentists must have write permission to manage clinic medication catalog."""
    manifest = MedicationCatalogModule.manifest
    role_perms = manifest.get("role_permissions", {})
    assert "write" in role_perms.get("dentist", []), "Dentist must have write permission"


@pytest.mark.asyncio
async def test_search_nomenclature_db_empty_result_does_not_fallback():
    """When DB has records, a non-matching query returns empty list without reading JSON."""
    mock_db = AsyncMock()
    mock_count = MagicMock()
    mock_count.scalar.return_value = 4636  # DB is seeded

    mock_rows = MagicMock()
    mock_rows.scalars.return_value.all.return_value = []

    # First call: count, second call: select
    mock_db.execute.side_effect = [mock_count, mock_rows]

    results = await MedicationCatalogService.search_nomenclature(mock_db, q="nonexistentdrugxyz", limit=10)
    assert results == []
    assert mock_db.execute.await_count == 2
