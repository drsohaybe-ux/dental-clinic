"""clinic.created handler — seed the clinic's medical reference lists.

Own-session (issue #183 precedent from ``catalog``): ``clinic.created``
is published after the signup transaction commits and without a session,
so the seeder runs on its own connection and must be non-transactional.
``seed_medical_reference`` is idempotent; failures are logged, never raised —
``POST /medical_reference/seed`` repairs empty lists on demand.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.database import async_session_maker

logger = logging.getLogger(__name__)


async def on_clinic_created(data: dict[str, Any]) -> None:
    clinic_id_raw = data.get("clinic_id")
    if not clinic_id_raw:
        return
    try:
        clinic_id = UUID(str(clinic_id_raw))
    except (ValueError, TypeError):
        return

    from .seed import seed_medical_reference

    async with async_session_maker() as db:
        try:
            summary = await seed_medical_reference(db, clinic_id)
            await db.commit()
            logger.info("medical_reference.on_clinic_created seeded %s for %s", summary, clinic_id)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("medical_reference seeding failed for %s: %s", clinic_id, exc)
            await db.rollback()
