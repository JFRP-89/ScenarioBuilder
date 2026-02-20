"""Infrastructure bootstrap / composition root.

Wires up all use cases with their infrastructure dependencies.

Environment modes
-----------------
``APP_ENV`` controls production vs development behaviour:

* ``APP_ENV=prod``  — strict fail-fast, no fallbacks, no demo seeding.
* Any other value   — development/test mode with graceful fallbacks.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

# Load .env early so DATABASE_URL is available
try:
    from dotenv import load_dotenv

    load_dotenv(override=False)
except ImportError:
    pass

# Use cases
from application.use_cases.create_variant import CreateVariant
from application.use_cases.delete_card import DeleteCard
from application.use_cases.generate_scenario_card import GenerateScenarioCard
from application.use_cases.get_card import GetCard
from application.use_cases.list_cards import ListCards
from application.use_cases.list_favorites import ListFavorites
from application.use_cases.render_map_svg import RenderMapSvg
from application.use_cases.save_card import SaveCard
from application.use_cases.toggle_favorite import ToggleFavorite

# Infrastructure generators
from infrastructure.generators.secure_seed_generator import SecureSeedGenerator
from infrastructure.generators.uuid_id_generator import UuidIdGenerator

# Infrastructure rendering
from infrastructure.maps.svg_map_renderer import SvgMapRenderer

# Infrastructure repositories
from infrastructure.repositories.in_memory_card_repository import InMemoryCardRepository
from infrastructure.repositories.in_memory_favorites_repository import (
    InMemoryFavoritesRepository,
)

# Infrastructure scenario generation
from infrastructure.scenario_generation.basic_scenario_generator import (
    BasicScenarioGenerator,
)

logger = logging.getLogger(__name__)

# Module-level singleton: shared by Flask and Gradio in the combined app.
_services_holder: list["Services | None"] = [None]

_LOG_BACKEND_IN_MEMORY = "Using SessionStore backend: in_memory"


# =============================================================================
# ENVIRONMENT HELPERS
# =============================================================================
def _get_env(name: str, default: str = "") -> str:
    """Read an environment variable, stripped of whitespace."""
    return os.environ.get(name, default).strip()


def _is_prod() -> bool:
    """Return ``True`` when ``APP_ENV`` equals ``prod``."""
    return _get_env("APP_ENV") == "prod"


def get_services() -> "Services":
    """Return the shared Services singleton.

    Raises ``RuntimeError`` if ``build_services()`` has not been called yet.
    """
    if _services_holder[0] is None:
        raise RuntimeError("Services not initialised — call build_services() first.")
    return _services_holder[0]


# =============================================================================
# SESSION STORE WIRING
# =============================================================================
def _build_session_store() -> None:
    """Configure session store backend based on ``DATABASE_URL`` and ``APP_ENV``.

    Production (``APP_ENV=prod``)
        Every step must succeed or a ``RuntimeError`` is raised so the
        process exits immediately with a clear message.

    Development / test (any other ``APP_ENV``)
        Failures are logged as warnings and the in-memory session store
        is used as a fallback.
    """
    prod = _is_prod()
    database_url = _get_env("DATABASE_URL")

    # --- 1) DATABASE_URL must be present in prod --------------------------
    if not database_url:
        if prod:
            raise RuntimeError(
                "Production requires PostgresSessionStore. "
                "Reason: DATABASE_URL is not set."
            )
        logger.info("%s (no DATABASE_URL)", _LOG_BACKEND_IN_MEMORY)
        return

    # --- 2) Must be a PostgreSQL URL --------------------------------------
    if not database_url.startswith("postgres"):
        if prod:
            raise RuntimeError(
                "Production requires PostgresSessionStore. "
                "Reason: DATABASE_URL is not a PostgreSQL URL."
            )
        logger.warning(
            "DATABASE_URL is not a PostgreSQL URL — "
            "falling back to in-memory session store."
        )
        logger.info(_LOG_BACKEND_IN_MEMORY)
        return

    # --- 3) SQLAlchemy / psycopg2 must be importable ---------------------
    try:
        from infrastructure.auth.postgres_session_store import PostgresSessionStore
        from infrastructure.auth.session_store import configure_store
        from infrastructure.db.session import SessionLocal
    except ImportError as exc:
        if prod:
            raise RuntimeError(
                "Production requires PostgresSessionStore. "
                f"Reason: required dependency not installed — {exc}"
            ) from exc
        logger.warning(
            "DATABASE_URL set to postgres but SQLAlchemy/psycopg2 is not "
            "installed. Falling back to in-memory session store."
        )
        logger.info(_LOG_BACKEND_IN_MEMORY)
        return

    # --- 4) DB must be reachable ------------------------------------------
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
    except (OSError, RuntimeError) as exc:
        if prod:
            raise RuntimeError(
                "Production requires PostgresSessionStore. "
                f"Reason: cannot connect to PostgreSQL — {exc}"
            ) from exc
        logger.warning(
            "Session store: cannot connect to PostgreSQL — %s. "
            "Falling back to in-memory session store.",
            exc,
        )
        logger.info(_LOG_BACKEND_IN_MEMORY)
        return

    store = PostgresSessionStore(session_factory=SessionLocal)
    configure_store(store)
    logger.info("Using SessionStore backend: postgres")


# =============================================================================
# SERVICES CONTAINER
# =============================================================================
@dataclass(frozen=True)
class Services:
    """Container for all application use cases."""

    # Core use cases
    generate_scenario_card: GenerateScenarioCard
    save_card: SaveCard
    get_card: GetCard

    # Optional use cases
    list_cards: ListCards
    toggle_favorite: ToggleFavorite
    list_favorites: ListFavorites
    create_variant: CreateVariant
    render_map_svg: RenderMapSvg
    delete_card: DeleteCard


# =============================================================================
# COMPOSITION ROOT
# =============================================================================
def _build_card_repository():
    """Select CardRepository backend based on DATABASE_URL.

    - If DATABASE_URL is set and starts with 'postgres' → PostgresCardRepository.
    - Otherwise → InMemoryCardRepository (default for dev/test).

    SQLAlchemy imports are deferred to avoid import errors when the dependency
    is not installed (e.g., in lightweight test environments).
    """
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres"):
        try:
            from infrastructure.db.session import SessionLocal
            from infrastructure.repositories.postgres_card_repository import (
                PostgresCardRepository,
            )
        except ImportError:
            logger.warning(
                "DATABASE_URL set to postgres but SQLAlchemy is not installed. "
                "Falling back to in-memory repository."
            )
            return InMemoryCardRepository()

        logger.info("Using CardRepository backend: postgres")
        return PostgresCardRepository(session_factory=SessionLocal)

    logger.info("Using CardRepository backend: in_memory")
    return InMemoryCardRepository()


def _build_favorites_repository():
    """Select FavoritesRepository backend based on DATABASE_URL.

    Mirrors _build_card_repository() logic: postgres when DATABASE_URL is set,
    in-memory otherwise.
    """
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres"):
        try:
            from infrastructure.db.session import SessionLocal
            from infrastructure.repositories.postgres_favorites_repository import (
                PostgresFavoritesRepository,
            )
        except ImportError:
            logger.warning(
                "DATABASE_URL set to postgres but SQLAlchemy is not installed. "
                "Falling back to in-memory favorites repository."
            )
            return InMemoryFavoritesRepository()

        logger.info("Using FavoritesRepository backend: postgres")
        return PostgresFavoritesRepository(session_factory=SessionLocal)

    logger.info("Using FavoritesRepository backend: in_memory")
    return InMemoryFavoritesRepository()


def build_services() -> Services:
    """Build and wire all use cases with their dependencies.

    Each call to build_services() creates independent instances
    with their own repository state.

    Returns:
        Services container with all use cases wired up.
    """
    # 0) Configure session store backend (postgres or in-memory)
    _build_session_store()

    # 0b) Seed demo users (dev only, opt-in via SEED_DEMO_USERS=1)
    seed_requested = _get_env("SEED_DEMO_USERS") in ("1", "true", "yes")
    if seed_requested and _is_prod():
        logger.warning("SEED_DEMO_USERS ignored in production")
    elif seed_requested:
        try:
            from infrastructure.auth.user_store import seed_demo_users_to_database

            seed_demo_users_to_database()
            logger.info("Demo users seeded successfully.")
        except (ImportError, OSError, RuntimeError):
            logger.debug("Failed to seed demo users — skipping.", exc_info=True)

    # 1) Build infrastructure dependencies
    card_repo = _build_card_repository()
    favorites_repo = _build_favorites_repository()
    id_gen = UuidIdGenerator()
    seed_gen = SecureSeedGenerator()
    scenario_gen = BasicScenarioGenerator()
    renderer = SvgMapRenderer()

    # 2) Build use cases with dependencies
    generate_scenario_card = GenerateScenarioCard(
        id_generator=id_gen,
        seed_generator=seed_gen,
        scenario_generator=scenario_gen,
        card_repository=card_repo,
    )

    save_card = SaveCard(repository=card_repo)

    get_card = GetCard(repository=card_repo)

    list_cards = ListCards(repository=card_repo)

    toggle_favorite = ToggleFavorite(
        card_repository=card_repo,
        favorites_repository=favorites_repo,
    )

    list_favorites = ListFavorites(
        card_repository=card_repo,
        favorites_repository=favorites_repo,
    )

    create_variant = CreateVariant(
        repository=card_repo,
        id_generator=id_gen,
        seed_generator=seed_gen,
        scenario_generator=scenario_gen,
    )

    render_map_svg = RenderMapSvg(
        repository=card_repo,
        renderer=renderer,
    )

    delete_card = DeleteCard(
        repository=card_repo,
        favorites_repository=favorites_repo,
    )

    # 3) Build services container and cache as singleton
    svc = Services(
        generate_scenario_card=generate_scenario_card,
        save_card=save_card,
        get_card=get_card,
        list_cards=list_cards,
        toggle_favorite=toggle_favorite,
        list_favorites=list_favorites,
        create_variant=create_variant,
        render_map_svg=render_map_svg,
        delete_card=delete_card,
    )
    _services_holder[0] = svc
    return svc
