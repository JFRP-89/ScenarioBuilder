# Arquitectura — Scenario Builder

## Visión general

Scenario Builder sigue una **Clean Architecture** (Uncle Bob) implementada como
**monolito modular** con cuatro capas concéntricas.  
El principio rector es la **Inversión de Dependencias (DIP)**: las capas internas
definen interfaces (*ports*) y las externas las implementan (*adapters*).

```
┌──────────────────────────────────────────────────┐
│            Adapters (HTTP / UI)                  │  ← Frameworks
│   Flask blueprints · Gradio handlers · CSS       │
├──────────────────────────────────────────────────┤
│           Application (Use Cases)                │  ← Orquestación
│   DTOs · .execute() · Ports (Protocol)           │
├──────────────────────────────────────────────────┤
│         Infrastructure (Implementación)          │  ← Tecnología
│   Repos · Auth · SVG renderer · Bootstrap        │
├──────────────────────────────────────────────────┤
│             Domain (Reglas puras)                │  ← Negocio
│   Card · MapSpec · TableSize · AuthZ · Scoring   │
└──────────────────────────────────────────────────┘
```

El flujo de datos atraviesa las capas de fuera hacia dentro:

```
Usuario → Adapter → Use Case → Domain  (ida)
           ↑                      ↓
         Adapter ← Use Case ← Domain  (vuelta)
```

---

## Capas en detalle

### 1. Domain (`src/domain/`)

Reglas de negocio puras sin dependencias externas (solo stdlib).

| Módulo | Responsabilidad |
|--------|----------------|
| `cards/card.py` | Entidad `Card` (frozen dataclass). Post-init valida IDs, seed, tipos, coherencia tabla-mapa. Anti-IDOR: métodos `can_user_read()` / `can_user_write()`. |
| `cards/models.py` | Value objects `CardItem` y `ScenarioCard` (frozen dataclasses). Representan elementos de contenido del juego. |
| `cards/generator.py` | `generate_card()` — generación determinista con RNG seeded. Selecciona layout, deployment, objective, twist, story_hook, constraints. |
| `cards/constraints.py` | `incompatible_pairs_ok()` — verifica que pares incompatibles no coexistan en la selección. |
| `cards/scoring.py` | `matched_score()` — puntuación base 100, penaliza −10 por cada risk flag (floor 0). |
| `cards/card_validation.py` | Validaciones de seed (rechaza bool, negativo), IDs (non-empty), tipos, coherencia tabla. |
| `cards/card_content_validation.py` | Validación de objectives (str/dict), special_rules (list[dict]), visibility+shared_with. |
| `maps/table_size.py` | `TableSize` (frozen dataclass). Dimensiones en mm internamente; factory methods `from_cm()`, `from_in()`, `from_ft()`. Presets: standard (120×120 cm), massive (180×120 cm). Rango: 60–300 cm. |
| `maps/map_spec.py` | `MapSpec` (frozen dataclass). Contiene shapes, objective_shapes, deployment_shapes. Post-init valida conteos, bounds, balance y deployment rules. |
| `maps/spec.py` | `TABLE_PRESETS`, `validate_table_size()`, `validate_map_spec()` con helpers para rect/circle. |
| `maps/collision.py` | Detección de colisiones entre shapes (geometría 2D). |
| `security/authz.py` | `Visibility` enum (PRIVATE/SHARED/PUBLIC), `can_read()`, `can_write()`, `parse_visibility()`. Modelo deny-by-default. |
| `errors.py` | Jerarquía: `DomainError` → `ValidationError`, `NotFoundError`, `ForbiddenError`. |
| `validation.py` | `validate_non_empty_str()` — utilidad compartida. |
| `seed.py` | `MAX_SEED` (2³¹−1), `get_rng()` (deterministic), `normalize_seed()`, `derive_attempt_seed()` (SHA-256). |

**Invariantes de diseño:**
- Zero imports de otras capas.
- 100 % cobertura de tests obligatoria.
- Los errores son siempre `ValidationError`; nunca códigos HTTP.
- Todos los dataclasses son `frozen` (inmutables).

### 2. Application (`src/application/`)

Orquesta la lógica de negocio definiendo **use cases** y **ports**.

#### Ports (interfaces — `application/ports/`)

| Port (Protocol) | Métodos |
|------------------|---------|
| `CardRepository` | `save()`, `get_by_id()`, `find_by_seed()`, `delete()`, `list_all()`, `list_for_owner()` |
| `FavoritesRepository` | `is_favorite()`, `set_favorite()`, `list_favorites()`, `remove_all_for_card()` |
| `IdGenerator` | `generate_card_id() → str` |
| `SeedGenerator` | `generate_seed() → int`, `calculate_from_config()` |
| `ScenarioGenerator` | `generate_shapes(seed, table, mode) → list[dict]` |
| `MapRenderer` | `render_svg()`, `render()` |
| `ContentProvider` | `get_layouts()`, `get_deployments()`, `get_objectives()`, `get_twists()`, `get_story_hooks()`, `get_constraints()` |

#### Use Cases (`application/use_cases/`)

Todos siguen el patrón **Request DTO → `.execute()` → Response DTO** con
validación de `actor_id` y anti-IDOR.

| Use Case | Descripción |
|----------|------------|
| `GenerateScenarioCard` | Genera escenario completo (seed, shapes, contenido MESBG). |
| `SaveCard` | Persiste una Card; owner-only. |
| `GetCard` | Obtiene Card por ID; verifica visibilidad. |
| `ListCards` | Lista cards filtradas (mine / public / shared_with_me). |
| `DeleteCard` | Elimina card + limpia favoritos; owner-only. |
| `CreateVariant` | Clona card con nuevo seed/id; owner-only sobre base. |
| `ToggleFavorite` | Añade/quita favorito; requiere acceso de lectura. |
| `ListFavorites` | Devuelve favoritos del actor; limpia stale entries. |
| `RenderMapSvg` | Genera SVG vía MapRenderer port; anti-IDOR. |
| `manage_presets` | Devuelve presets de mesa (standard, massive). |

**Invariantes de diseño:**
- Importa solo `domain/`. Nunca `infrastructure/` ni `adapters/`.
- Define ports como `Protocol` (typing).
- ≥ 80 % cobertura de tests obligatoria.

### 3. Infrastructure (`src/infrastructure/`)

Implementa los ports con tecnología concreta y contiene el **composition root**.

| Módulo | Implementa | Tecnología |
|--------|-----------|-----------|
| `repositories/in_memory_card_repository.py` | `CardRepository` | `dict` en memoria |
| `repositories/postgres_card_repository.py` | `CardRepository` | SQLAlchemy + PostgreSQL |
| `repositories/in_memory_favorites_repository.py` | `FavoritesRepository` | `dict` en memoria |
| `repositories/postgres_favorites_repository.py` | `FavoritesRepository` | SQLAlchemy + PostgreSQL |
| `generators/uuid_id_generator.py` | `IdGenerator` | `uuid.uuid4()` |
| `generators/secure_seed_generator.py` | `SeedGenerator` | `secrets.randbits(31)` |
| `generators/deterministic_seed_generator.py` | – | Hash determinista |
| `maps/svg_map_renderer.py` | `MapRenderer` | SVG builder (7 capas) |
| `maps/_renderer/` | – | Geometría, overlay, primitivas, sanitización |
| `content/file_content_provider.py` | `ContentProvider` | JSON desde `content/mesbg/` |
| `auth/auth_service.py` | – | Autenticación, sesiones, perfiles |
| `auth/user_store.py` | – | CRUD usuarios + lockout |
| `auth/session_store.py` | – | Sesiones en memoria |
| `auth/postgres_session_store.py` | – | Sesiones en PostgreSQL |
| `auth/validators.py` | – | Allowlist de inputs auth |
| `db/models.py` | – | Modelos SQLAlchemy (CardModel, UserModel, SessionModel, FavoritesModel) |
| `db/session.py` | – | Session factory SQLAlchemy |
| `config.py` | – | `get_env()` helper |

#### Composition Root — `bootstrap.py`

```python
class Services:
    generate_scenario_card: GenerateScenarioCard
    save_card: SaveCard
    get_card: GetCard
    list_cards: ListCards
    toggle_favorite: ToggleFavorite
    list_favorites: ListFavorites
    create_variant: CreateVariant
    render_map_svg: RenderMapSvg
    delete_card: DeleteCard

def build_services() -> Services:
    """Construye todo el grafo de dependencias.
    - Producción (DATABASE_URL set): PostgreSQL para todo.
    - Desarrollo: Fallback graceful a in-memory.
    Resultado cacheado como singleton."""
```

Regla: los adapters solo obtienen servicios vía `build_services()`.  
Nunca instancian repos/use-cases a mano.

### 4. Adapters (`src/adapters/`)

Exponen la lógica al mundo exterior sin contener reglas de negocio.

#### Flask (`adapters/http_flask/`)

API REST con blueprints modulares:

| Blueprint | Base Path | Endpoints |
|-----------|-----------|-----------|
| `auth_bp` | `/auth` | `POST /login`, `POST /logout`, `GET /me`, `POST /reauth`, `POST /profile`, `POST /register`, `GET /check-username` |
| `cards_bp` | `/cards` | `POST /`, `GET /`, `GET /<id>`, `PUT /<id>`, `DELETE /<id>`, `GET /<id>/map.svg` |
| `favorites_bp` | `/favorites` | `POST /<card_id>/toggle`, `GET /` |
| `health` | `/health` | `GET /` |
| `presets` | `/presets` | `GET /` |

Módulos de soporte:
- `error_contract.py` — Mapeo `ValidationError → 400`, `NotFoundError → 404`, `ForbiddenError → 403`.
- `svg_sanitizer.py` — Allowlist de tags SVG, `defusedxml`, prevención XSS/XXE.
- `middleware.py` — Extracción de headers (`X-Actor-Id`, `X-Session-Id`, `X-CSRF-Token`).
- `context.py` — Request context helpers.

#### Gradio (`adapters/ui_gradio/`)

Interfaz web declarativa con el patrón **facade + internal modules**:

```
ui/wiring/
├── wire_detail.py              ← Facade (250-450 líneas)
├── wire_deployment_zones.py
├── wire_generate.py
├── wire_scenography.py
├── wire_table_config.py
├── wire_constraints.py
├── wire_special_rules.py
├── wire_sharing.py
├── wire_visibility.py
├── wire_favorites.py
├── wire_gallery.py
├── wire_seed.py
├── wire_header.py
├── wire_mode.py
├── wire_auth.py
├── _detail/                    ← Módulos internos
│   ├── _render.py
│   └── _converters.py
├── _deployment/
│   ├── _form_state.py
│   ├── _geometry.py
│   ├── _ui_updates.py
│   └── _zone_builder.py
├── _scenography/
│   ├── _form_state.py
│   ├── _polygon.py
│   ├── _ui_updates.py
│   └── _builder.py
└── _generate/
    ├── _preview.py
    ├── _create_logic.py
    ├── _resets.py
    └── _outputs.py
```

Módulos de soporte:
- `api_client.py` — HTTP client hacia la API Flask.
- `payload_builders.py` — Constructores de payloads JSON.
- `state_helpers.py` — Gestión de estado Gradio.
- `units.py` — Conversión de unidades (cm/in/ft).
- `auth/` — Login/logout/profile UI con lockout.
- `builders/` — Constructores de componentes Gradio.
- `handlers/` — Event handlers.
- `services/` — Lógica de negocio UI-side.

#### App combinada (`adapters/combined_app.py`)

```python
def create_combined_app() -> FastAPI:
    """ASGI unificada:
    - Flask (WSGI) vía WSGIMiddleware en /
    - Gradio UI montada en /sb/
    - Redirects: / → /sb/, /ui/ → /sb/ (legacy)
    """
```

---

## Política de imports

```
domain/         → (nada)
application/    → domain/
infrastructure/ → domain/ + application/
adapters/       → domain/ + application/ + infrastructure/
```

**Prohibido**: `src.` como prefijo de imports. Nunca importar hacia dentro
(application → infrastructure, domain → application).

---

## Flujo de datos — Ejemplo: crear card

```
1. Usuario envía POST /cards
2. Flask adapter: parsea JSON, extrae actor_id del header
3. SaveCard.execute(SaveCardRequest)
4. Use case: valida actor_id, construye Card (domain)
5. Card.__post_init__: valida seed, IDs, tipos, coherencia tabla
6. Use case: llama repo.save(card) — port
7. Repo PostgreSQL: INSERT INTO cards (...)
8. Use case: retorna SaveCardResponse(card_id)
9. Flask adapter: retorna 201 {"card_id": "..."}
```

---

## Decisiones clave

| Decisión | Justificación |
|----------|--------------|
| Monolito modular (no microservicios) | Producto en fase MVP; un solo equipo; despliegue sencillo. |
| Python 3.11+ | Pattern matching, type hints mejorados, rendimiento. |
| Frozen dataclasses | Inmutabilidad garantiza seguridad en concurrencia y simplifica reasoning. |
| Dual persistence (memory + PostgreSQL) | Desarrollo local sin DB; producción con PostgreSQL. Mismo contrato via ports. |
| SVG (no Canvas/raster) | Escalable sin pérdida; imprimible a tamaño real de mesa. |
| Flask + Gradio en un solo proceso | Mismas cookies/sesiones; sin CORS; deploy simplificado. |
| Facade pattern en wiring | Previene god-modules; cada facade < 450 líneas con helpers testables. |
| Seeds deterministas (SHA-256) | Reproducibilidad: mismo seed = mismo escenario siempre. |

---

## Diagrama de módulos

```
src/
├── domain/
│   ├── cards/          Card, CardItem, ScenarioCard, generator, scoring, constraints
│   ├── maps/           TableSize, MapSpec, spec, collision
│   ├── security/       Visibility, can_read, can_write (deny-by-default)
│   ├── errors.py       DomainError → ValidationError, NotFoundError, ForbiddenError
│   ├── validation.py   validate_non_empty_str
│   └── seed.py         MAX_SEED, get_rng, normalize_seed, derive_attempt_seed
│
├── application/
│   ├── ports/          CardRepository, FavoritesRepository, IdGenerator, SeedGenerator,
│   │                   ScenarioGenerator, MapRenderer, ContentProvider
│   └── use_cases/      10 use cases (Request DTO → execute → Response DTO)
│
├── infrastructure/
│   ├── repositories/   InMemory + Postgres (Card, Favorites)
│   ├── generators/     UuidIdGenerator, SecureSeedGenerator, DeterministicSeedGenerator
│   ├── maps/           SvgMapRenderer + _renderer/ (7 capas SVG)
│   ├── content/        FileContentProvider (JSON desde content/mesbg/)
│   ├── auth/           AuthService, UserStore, SessionStore, validators
│   ├── db/             SQLAlchemy models (CardModel, UserModel, SessionModel, FavoritesModel)
│   ├── bootstrap.py    Composition root → build_services()
│   └── config.py       get_env()
│
└── adapters/
    ├── http_flask/     API REST (blueprints: auth, cards, favorites, health, presets)
    ├── ui_gradio/      Gradio UI (15 facades, 4 internal packages, auth module)
    └── combined_app.py FastAPI wrapper (Flask WSGI + Gradio mount)
```
