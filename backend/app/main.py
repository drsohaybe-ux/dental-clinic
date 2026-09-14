"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth.router import limiter
from app.core.auth.router import router as auth_router
from app.core.log_context import (
    new_request_id,
    reset_request_context,
    set_request_context,
    setup_logging,
)
from app.core.plugins.loader import mount_modules, register_discovered
from app.core.plugins.processor import PendingProcessor
from app.core.plugins.service import ModuleService
from app.core.scheduler import init_scheduler, shutdown_scheduler
from app.core.schemas import ErrorResponse
from app.database import async_session_maker, engine, get_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Logging: attach the context filter early so every line emitted
    # during startup / module install also carries the bound fields
    # (defaults to ``-`` outside a request).
    setup_logging()

    # Startup — discover everything, settle DB state, then mount only what
    # is installed (issue #91). Order matters: the processor may install or
    # remove modules in this very boot, and the mount step reads the result.
    discovered = register_discovered()

    # Sync in-memory registry into core_module (best-effort).
    try:
        async with async_session_maker() as session:
            await ModuleService(session).reconcile_with_db()
    except Exception:
        logger.exception("Module registry reconciliation failed at startup")

    # Process pending install/uninstall/upgrade operations.
    try:
        processor = PendingProcessor(async_session_maker)
        processed = await processor.run()
        if processed:
            logger.info("Processed pending module operations: %s", processed)
    except Exception:
        logger.exception("Pending module processor raised")

    # Ensure treatment price snapshots and planned sessions match Algerian DZD catalog prices.
    try:
        async with async_session_maker() as session:
            await session.execute(
                text("""
                    UPDATE treatments t
                    SET price_snapshot = tci.default_price
                    FROM treatment_catalog_items tci
                    WHERE t.catalog_item_id = tci.id
                      AND tci.default_price IS NOT NULL
                      AND (t.price_snapshot IS NULL OR t.price_snapshot < 1000);

                    UPDATE planned_treatment_item_sessions ptis
                    SET amount = cis.default_price
                    FROM planned_treatment_items pti
                    JOIN treatments t ON pti.treatment_id = t.id
                    JOIN catalog_item_sessions cis ON cis.catalog_item_id = t.catalog_item_id AND cis.sequence = ptis.sequence
                    WHERE ptis.plan_item_id = pti.id
                      AND cis.default_price IS NOT NULL
                      AND ptis.amount < 1000;

                    UPDATE planned_treatment_item_sessions ptis
                    SET amount = tci.default_price
                    FROM planned_treatment_items pti
                    JOIN treatments t ON pti.treatment_id = t.id
                    JOIN treatment_catalog_items tci ON t.catalog_item_id = tci.id
                    WHERE ptis.plan_item_id = pti.id
                      AND tci.default_price IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM catalog_item_sessions cis
                          WHERE cis.catalog_item_id = t.catalog_item_id AND cis.sequence = ptis.sequence
                      )
                      AND ptis.amount < 1000;
                """)
            )
            await session.commit()
    except Exception:
        logger.exception("Price snapshot self-healing failed at startup")

    # Ensure clinic branding, doctor identity, and demo patients match Algerian presentation data (Arselane Dental Clinic, Skikda)
    try:
        import json
        async with async_session_maker() as session:
            is_pg = session.bind and session.bind.dialect.name == "postgresql"
            clinic_addr = json.dumps({
                "street": "Boulevard Didouche Mourad",
                "city": "Skikda",
                "postal_code": "21000",
                "country": "Algérie"
            })
            if is_pg:
                await session.execute(
                    text("""
                        UPDATE clinics
                        SET name = 'Arselane Dental Clinic',
                            address = CAST(:addr AS jsonb),
                            phone = '+213 38 72 15 20',
                            email = 'contact@arselane-dental.dz',
                            currency = 'DZD',
                            timezone = 'Africa/Algiers'
                        WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
                    """),
                    {"addr": clinic_addr}
                )
            else:
                await session.execute(
                    text("""
                        UPDATE clinics
                        SET name = 'Arselane Dental Clinic',
                            address = :addr,
                            phone = '+213 38 72 15 20',
                            email = 'contact@arselane-dental.dz',
                            currency = 'DZD',
                            timezone = 'Africa/Algiers'
                        WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
                    """),
                    {"addr": clinic_addr}
                )

            # Update users
            await session.execute(
                text("""
                    UPDATE users
                    SET first_name = 'Dr.', last_name = 'Arselane'
                    WHERE email IN ('admin@demo.clinic', 'dentist@demo.clinic')
                       OR id IN ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a23');
                """)
            )

            # Update 15 demo patients
            algerian_patients = [
                ("d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a40", "Mohamed", "Benali", "+213 550 12 34 01", "mohamed.benali@email.dz", "Patient pédiatrique. Première visite pour contrôle.", "Skikda", "Boulevard Didouche Mourad"),
                ("d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a41", "Amira", "Mansouri", "+213 661 23 45 02", "amira.mansouri@email.dz", "Traitement d'orthodontie en cours.", "Skikda", "Cité 20 Août 1955"),
                ("d2eebc99-9c0b-4ef8-bb6d-6bb9bd380a42", "Karim", "Haddad", "+213 770 34 56 03", "karim.haddad@email.dz", "Sensibilité dentaire au froid secteur 2.", "Skikda", "Avenue Zighout Youcef"),
                ("d3eebc99-9c0b-4ef8-bb6d-6bb9bd380a43", "Fatima Zohra", "Bouzid", "+213 551 45 67 04", "fatima.bouzid@email.dz", "Contrôle semestriel. Bonne hygiène bucco-dentaire.", "Collo", "Route de Collo"),
                ("d4eebc99-9c0b-4ef8-bb6d-6bb9bd380a44", "Yacine", "Merabet", "+213 662 56 78 05", "yacine.merabet@email.dz", "Prothèse amovible à réajuster.", "Skikda", "Cité Frères Saker"),
                ("d5eebc99-9c0b-4ef8-bb6d-6bb9bd380a45", "Amina", "Belkacem", "+213 771 67 89 06", "amina.belkacem@email.dz", "Blanchiment dentaire souhaité.", "El Harrouch", "Boulevard des Martyrs"),
                ("d6eebc99-9c0b-4ef8-bb6d-6bb9bd380a46", "Nabil", "Saidi", "+213 552 78 90 07", "nabil.saidi@email.dz", "Patient diabétique. Contrôle spécial de cicatrisation.", "Skikda", "Rue de l'ALN"),
                ("d7eebc99-9c0b-4ef8-bb6d-6bb9bd380a47", "Rachid", "Khelifi", "+213 663 89 01 08", "rachid.khelifi@email.dz", "Pose d'implant dentaire secteur 4.", "Azzaba", "Avenue de l'Indépendance"),
                ("d8eebc99-9c0b-4ef8-bb6d-6bb9bd380a48", "Samira", "Bencheikh", "+213 772 90 12 09", "samira.bencheikh@email.dz", "Détartrage et polissage annuel.", "Skikda", "Cité Zeramna"),
                ("d9eebc99-9c0b-4ef8-bb6d-6bb9bd380a49", "Khaled", "Meziani", "+213 553 01 23 10", "khaled.meziani@email.dz", "Hypertendu. Vérifier la tension avant les soins.", "Constantine", "Rue Larbi Ben M'hidi"),
                ("daeebc99-9c0b-4ef8-bb6d-6bb9bd380a4a", "Zineb", "Cherif", "+213 664 12 34 11", "zineb.cherif@email.dz", "Douleur dent de sagesse 38.", "Skikda", "Boulevard Houari Boumediene"),
                ("dbeebc99-9c0b-4ef8-bb6d-6bb9bd380a4b", "Walid", "Dahmani", "+213 773 23 45 12", "walid.dahmani@email.dz", "Consultation prothèse fixe.", "Skikda", "Cité Hamrouche Hamoudi"),
                ("dceebc99-9c0b-4ef8-bb6d-6bb9bd380a4c", "Soumia", "Taleb", "+213 554 34 56 13", "soumia.taleb@email.dz", "Gingivite de grossesse. Conseils d'hygiène.", "Annaba", "Avenue de l'ALN"),
                ("ddeebc99-9c0b-4ef8-bb6d-6bb9bd380a4d", "Anis", "Larbi", "+213 665 45 67 14", "anis.larbi@email.dz", "Scellement de sillons (sealants).", "Skikda", "Cité Merdj Eddib"),
                ("deeebc99-9c0b-4ef8-bb6d-6bb9bd380a4e", "Leila", "Zerrouki", "+213 774 56 78 15", "leila.zerrouki@email.dz", "Contrôle parodontal trimestriel.", "Skikda", "Rue Bachir Boukadoum"),
            ]

            for pid, fn, ln, ph, em, nt, city, street in algerian_patients:
                paddr = json.dumps({"street": street, "city": city, "postal_code": "21000", "country": "Algérie"})
                if is_pg:
                    await session.execute(
                        text("""
                            UPDATE patients
                            SET first_name = :fn,
                                last_name = :ln,
                                phone = :ph,
                                email = :em,
                                notes = :nt,
                                address = CAST(:paddr AS jsonb)
                            WHERE id = :pid;
                        """),
                        {"fn": fn, "ln": ln, "ph": ph, "em": em, "nt": nt, "paddr": paddr, "pid": pid}
                    )
                else:
                    await session.execute(
                        text("""
                            UPDATE patients
                            SET first_name = :fn,
                                last_name = :ln,
                                phone = :ph,
                                email = :em,
                                notes = :nt,
                                address = :paddr
                            WHERE id = :pid;
                        """),
                        {"fn": fn, "ln": ln, "ph": ph, "em": em, "nt": nt, "paddr": paddr, "pid": pid}
                    )

            await session.commit()
    except Exception:
        logger.exception("Arselane clinic and Algerian demo patient self-healing failed at startup")

    # Not best-effort: if the DB is unreachable here, booting with zero
    # modules would serve a healthy-looking but empty API. Let it raise —
    # the container restarts and retries, as it already does when the
    # entrypoint's migrations fail.
    async with async_session_maker() as session:
        installed = await ModuleService.installed_names(session)
    mounted = mount_modules(app, [m for m in discovered if m.name in installed])
    logger.info(
        "Mounted %d/%d modules: %s", len(mounted), len(discovered), [m.name for m in mounted]
    )

    # Initialize scheduler for background jobs (active modules only)
    init_scheduler()

    yield

    # Shutdown
    shutdown_scheduler()
    await engine.dispose()


app = FastAPI(
    title="DentalPin API",
    description="Open source dental clinic management software",
    version="2.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS
allowed_origins = settings.allowed_origins_list.copy()
if settings.ENVIRONMENT == "development":
    allowed_origins.extend(
        [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Bind ``request_id`` for the lifetime of one HTTP request.

    Accepts an inbound ``X-Request-Id`` so a load balancer / client
    can correlate traces; otherwise mints a fresh short id. Echoes
    the value back on the response (success or error) so the caller
    can grep server logs. ``clinic_id`` / ``user_id`` are bound later
    by the auth dependency once they are known.
    """
    incoming = request.headers.get("x-request-id")
    rid = incoming if incoming and len(incoming) <= 64 else new_request_id()
    tokens = set_request_context(request_id=rid)
    try:
        response = await call_next(request)
    finally:
        reset_request_context(tokens)
    response.headers["X-Request-Id"] = rid
    return response


def _cors_headers(request: Request) -> dict[str, str]:
    # CORSMiddleware can't add headers to responses produced by exception
    # handlers (BaseHTTPMiddleware-based stacks lose the response when an
    # exception escapes). Without these headers, browsers report any 5xx
    # as a network error ("can't connect to server") instead of surfacing
    # the real status — which masks bugs and confuses users. So we mirror
    # CORSMiddleware's allow-list logic here for error responses.
    origin = request.headers.get("origin")
    if not origin:
        return {}
    if origin in allowed_origins or "*" in allowed_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }
    return {}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for HTTP exceptions using standard ErrorResponse format."""
    error_response = ErrorResponse(
        message=str(exc.detail),
        errors=[str(exc.detail)] if exc.detail else [],
    )
    headers = dict(exc.headers or {})
    headers.update(_cors_headers(request))
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers=headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.exception("Unhandled exception", exc_info=exc)
    if settings.ENVIRONMENT == "development":
        error_response = ErrorResponse(
            message=str(exc),
            errors=[str(exc)],
        )
    else:
        error_response = ErrorResponse(
            message="Internal server error",
            errors=[],
        )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
        headers=_cors_headers(request),
    )


# Mount auth router
app.include_router(auth_router, prefix="/api/v1")

# Mount module management router (install/uninstall/upgrade/restart).
from app.core.plugins.router import router as modules_router  # noqa: E402

app.include_router(modules_router, prefix="/api/v1")

# Mount AI agents infrastructure router (approval queue, audit, agent CRUD).
from app.core.agents.router import router as agents_router  # noqa: E402

app.include_router(agents_router, prefix="/api/v1")

# Mount omnichannel bridge router (n8n Webhook Ingestion & Telegram/WhatsApp Bridge)
from app.modules.omnichannel_bridge.router import router as omnichannel_bridge_router  # noqa: E402

app.include_router(omnichannel_bridge_router, prefix="/api/v1")

# Mount social automation router (n8n Studio Content & Social Posts)
from app.modules.social_automation.router import router as social_automation_router  # noqa: E402

app.include_router(social_automation_router, prefix="/api/v1/social_automation")
app.include_router(social_automation_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> JSONResponse:
    """Liveness probe — process is up.

    Used by the proxy/orchestrator to decide whether the container should
    receive traffic. Must NOT depend on the DB: a transient DB blip should
    not pull the backend out of the load balancer (we used to do that and
    Cloudflare ended up serving "no available server" until someone redeployed
    by hand).
    """
    return JSONResponse(content={"status": "healthy", "version": "2.0.0"})


@app.get("/health/ready")
async def readiness_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Readiness probe — schema is reachable.

    Probes a core table so monitoring catches the case where the DB volume
    gets recreated under a running container (schema gone, every business
    endpoint 500s). Recovery from that state belongs in the entrypoint
    (`dentalpin db upgrade`) plus an explicit container restart — not in
    the proxy healthcheck, since Docker's `restart: unless-stopped` does
    not auto-restart on healthcheck failure.
    """
    try:
        await db.execute(text("SELECT 1 FROM users LIMIT 1"))
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "unready", "version": "2.0.0", "error": str(exc)},
        )
    return JSONResponse(content={"status": "ready", "version": "2.0.0"})


@app.get("/api/v1")
async def api_root() -> dict:
    """API root endpoint."""
    return {
        "message": "DentalPin API",
        "version": "2.0.0",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None,
    }
