"""One-time / on-demand seeder script for the Algerian National Nomenclature.

Loads / refreshes the algerian_medications table from the cached JSON in <5 seconds.
Usage:
    python scripts/seed_algerian_nomenclature.py [--force]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time

# Ensure backend/ is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import async_session_maker
from app.modules.medication_catalog.seed_algeria import seed_algerian_nomenclature


async def run_seed(force: bool = False) -> None:
    start = time.time()
    print("Starting Algerian National Medication Nomenclature seeder...")
    async with async_session_maker() as db:
        summary = await seed_algerian_nomenclature(db, force_refresh=force)
        await db.commit()
    elapsed = time.time() - start
    print(
        f"Seeding finished in {elapsed:.2f}s: "
        f"{summary['seeded']} seeded, {summary['total']} total records."
    )


def main():
    parser = argparse.ArgumentParser(description="Seed Algerian medication nomenclature")
    parser.add_argument(
        "--force", action="store_true", help="Force refresh even if table is already populated"
    )
    args = parser.parse_args()
    asyncio.run(run_seed(force=args.force))


if __name__ == "__main__":
    main()
