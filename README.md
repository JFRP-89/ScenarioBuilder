# MESBG Scenario Card Generator

Generador de cartas de escenario para Middle-earth Strategy Battle Game (MESBG) con modos `casual`, `narrative` y `matched`.
Incluye generación determinista por `seed`, renderizado de **board layouts en SVG** con seguridad XSS/XXE, y gestión de favoritos.

> **Arquitectura limpia** con TDD + Security by Design. Ver [`AGENTS.md`](AGENTS.md) y [`context/`](context/) para reglas de desarrollo.

## Estado del proyecto

✅ **Funcional** — 2984 tests pasando (1887 unit + 1097 integration)  
🏗️ **Adaptadores**: Flask API + Gradio UI con composition root  
🔒 **Seguridad**: XSS/XXE mitigation en SVG, anti-IDOR en AuthZ, autenticación con cambio de contraseña  
📐 **Arquitectura**: Clean Architecture (domain → application → infrastructure → adapters)  
🔐 **Autenticación**: Login, registro, perfil con cambio de contraseña (PBKDF2-HMAC-SHA256, política fuerte)  
🗄️ **Persistencia**: PostgreSQL con Alembic migrations (cards, favorites, users, sessions)

## Stack técnico

- **Python 3.11+** (type hints con `|`, dataclasses)
- **Flask 2.x+** (API REST con Blueprints)
- **Gradio 4.x** (UI interactiva)
- **PostgreSQL** (persistencia con Alembic migrations)
- **Docker Compose** (orquestación)
- **pytest** (TDD: 60% unit, 30% integration, 10% e2e)
- **ruff** (lint), **defusedxml** (XXE prevention)

## Instalación y ejecución

### Desarrollo local

```bash
# Crear venv e instalar dependencias
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Ejecutar tests
pytest -q                     # Todos (2984 tests)
pytest tests/unit -q          # Solo unitarios (1887 tests)
pytest -q --cov=src --cov-report=term-missing  # Con coverage

# Linting
ruff check .
```

### Test profiles

The test suite supports two execution profiles:

**Profile A — local-dev (default)**
No PostgreSQL required. Tests marked `@pytest.mark.db` are auto-skipped.

```bash
pytest tests/unit tests/integration -q
# → 1887 passed (unit), ~61 skipped (DB integration)
```

**Profile B — with-db**
Requires a running PostgreSQL instance. Runs *all* tests including DB integration.

```bash
# 1. Start PostgreSQL (local or Docker)
# 2. Set env vars and run:
RUN_DB_TESTS=1 DATABASE_URL_TEST=postgresql://user:pass@localhost:5432/test_db \
  pytest tests/unit tests/integration -q
# → 2984 passed (1887 unit + 1097 integration con DB)
```

| Variable | Purpose |
|---|---|
| `RUN_DB_TESTS` | Set to `1` to enable DB tests |
| `DATABASE_URL_TEST` | PostgreSQL URL for test database |

> **Tip (Windows PowerShell):**
> ```powershell
> $env:RUN_DB_TESTS="1"
> $env:DATABASE_URL_TEST="postgresql://postgres:postgres@localhost:5434/scenario_test?client_encoding=utf8"
> pytest tests/unit tests/integration -q
> ```

### Docker

```bash
# Desplegar stack completo (PostgreSQL + app combinada)
docker compose up

# La aplicación combinada está disponible en:
# - http://localhost:8000          ← FastAPI + Flask/Gradio (unified)
# - http://localhost:8000/sb/      ← Gradio UI (con login y panel de perfil)
# - http://localhost:8000/auth/*   ← Flask auth endpoints
# - http://localhost:8000/health   ← Health check
```

## Interfaz Gradio — Funcionalidades

### Autenticación
- **Login**: Usuario y contraseña con validación
- **Registro**: Crear nueva cuenta con confirmación de contraseña
- **Check Username**: Verificación en tiempo real de disponibilidad  

### Perfil de Usuario
- **Mostrar**: Username, nombre, email
- **Editar**: Actualizar nombre y email
- **Cambiar Contraseña**: 
  - Campos "New Password" y "Confirm New Password" (opcionales)
  - Si ambos vacíos → guardar sin cambiar contraseña
  - Si alguno lleno → validar coincidencia + política fuerte
  - Campos se limpian automáticamente después de guardar o al abrir el panel
- **Logout**: Cerrar sesión desde el panel superior

## Estructura del proyecto

```
ScenarioBuilder/
├── src/
│   ├── domain/              # Reglas de negocio puras (no depende de nada)
│   │   ├── cards/           # Card, Visibility, GameMode
│   │   ├── maps/            # TableSize, MapSpec
│   │   └── security/        # Authorization (anti-IDOR)
│   ├── application/         # Casos de uso + ports (depende de domain)
│   │   ├── use_cases/       # CreateCard, GetCard, ToggleFavorite, etc.
│   │   └── ports/           # Interfaces (repos, generators)
│   ├── infrastructure/      # Implementaciones (depende de application)
│   │   ├── bootstrap.py     # Composition root (build_services)
│   │   ├── auth/            # Autenticación (user_store, auth_service, session_store, validators)
│   │   ├── repositories/    # In-memory repos (CardRepo, FavoritesRepo)
│   │   ├── generators/      # ID/Seed generators
│   │   └── maps/            # SVG renderers (con XSS/XXE mitigation)
│   └── adapters/            # HTTP/UI (depende de infrastructure)
│       ├── http_flask/      # Flask API (cards, favorites, maps, auth)
│       └── ui_gradio/       # Gradio UI (login, register, profile, cards)
├── content/                 # JSON editable (constraints, objectives, etc.)
├── tests/                   # TDD: 60% unit, 30% integration, 10% e2e
│   ├── unit/                # Tests de dominio y lógica pura (1500+)
│   ├── integration/         # Tests de adapters + repos (1300+)
│   └── e2e/                 # Tests end-to-end (11 smoke tests)
├── context/                 # Conocimiento para IA (arquitectura, calidad, security)
│   ├── agents/              # Guías para agentes especializados
│   ├── architecture/        # Layers, import policy, error model, facades
│   ├── quality/             # TDD, coverage, SOLID, definition-of-done
│   ├── security/            # Security by design, anti-IDOR, input validation, auth
│   └── workflow/            # Centaur mode, prompting
├── docs/                    # Documentación de evaluación
└── AGENTS.md                # Índice de reglas globales + punteros a context/
```

## API Flask — Endpoints

### Authentication

- `POST /auth/login` — Autenticar usuario (body: `{"username": "...", "password": "..."}`)
- `POST /auth/register` — Registrar nuevo usuario (body: `{"username": "...", "password": "...", "confirm_password": "...", "name": "...", "email": "..."}`)
- `GET /auth/check-username` — Verificar disponibilidad de username (query: `?username=...`)
- `POST /auth/logout` — Cerrar sesión
- `POST /auth/profile` — Actualizar perfil incluyendo cambio de contraseña (body: `{"name": "...", "email": "...", "new_password": "...", "confirm_new_password": "..."}`)
- `GET /auth/me` — Obtener perfil del usuario actual

**Headers**: 
- Obligatorio `X-CSRF-Token` en POST (incluido en cookies de sesión)
- Sesión almacenada en cookie `sb_session_id`

### Cards

- `POST /cards` — Crear card (body: `{"mode": "casual", "seed": 123}`)
- `GET /cards/<card_id>` — Obtener card
- `PUT /cards/<card_id>` — Actualizar card
- `DELETE /cards/<card_id>` — Eliminar card
- `GET /cards` — Listar cards del actor

**Header obligatorio**: `X-Actor-Id: <user_id>`

### Maps (SVG)

- `GET /cards/<card_id>/map.svg` — Renderizar mapa en SVG
  - **Seguridad**: defusedxml + allowlist + namespace stripping + CSP headers

### Favorites

- `POST /favorites/<card_id>/toggle` — Toggle favorite
- `GET /favorites` — Listar IDs de favoritos

### Health

- `GET /health` — Health check (no requiere auth)

## Modelos de dominio

### `TableSize`
- Dimensiones en mm (int)
- Presets: `standard()` 120×120 cm, `massive()` 180×120 cm
- Conversiones: `from_cm()`, `from_in()`, `from_ft()` con redondeo HALF_UP
- Límites: 60–300 cm por dimensión

### `MapSpec`
- Valida shapes: `circle`, `rect`, `polygon`
- Límites anti-abuso: ≤100 shapes, ≤200 puntos/polígono
- Coordenadas int dentro del tablero

### `Card`
- Identidad (ID, actor_id)
- Ownership/visibility (`Visibility`: private/shared/public)
- Modo de juego (`GameMode`: casual/narrative/matched)
- Seed determinista
- `TableSize` + `MapSpec`
- AuthZ: `can_user_read()`, `can_user_write()`

## Seguridad

### Principios (Security by Design)

- **Deny by default**: AuthZ explícita en cada operación
- **Anti-IDOR**: Validación de ownership en domain
- **Autenticación**:
  - Hash PBKDF2-HMAC-SHA256 (100k iteraciones, 32-byte salt)
  - Política de contraseña fuerte: 8+ chars, mayúscula, minúscula, número, carácter especial
  - Lockout: 3 intentos fallidos → bloqueado por 1 hora
  - Sesiones con timeout (24 horas activas, idle timeout)
- **XSS prevention**: 
  - int casting en SVG renderers
  - defusedxml para parsing seguro
  - Allowlist (bloquea `script`, `foreignObject`, `on*`, `javascript:`, `data:`)
  - CSP headers en respuestas
- **Input validation**: DTO validation en application, errores en domain

Ver [`context/security/`](context/security/) para detalles.

## Desarrollo — Reglas TDD

1. **RED**: Escribir tests que fallen (contrato)
2. **GREEN**: Implementar código mínimo para pasar
3. **REFACTOR**: Mejorar sin romper tests

**Coverage policy**: 100% domain, 80% application, 0% (opcional) adapters

Ver [`AGENTS.md`](AGENTS.md) y [`context/quality/tdd.md`](context/quality/tdd.md).

## Comandos útiles

```bash
# Tests
pytest -q                              # Suite completa
pytest tests/unit -q                   # Solo unitarios
pytest -k "test_card" -v               # Tests que matchean pattern
pytest --lf                            # Solo tests que fallaron antes

# Coverage
pytest --cov=src --cov-report=html     # Reporte HTML en htmlcov/

# Lint
ruff check .                           # Check
ruff check . --fix                     # Auto-fix

# Run
python -m flask --app src.adapters.http_flask.app run
python src/adapters/ui_gradio/app.py
```

## Migraciones (PostgreSQL)

La vía oficial para persistencia es **Alembic**. Para uso rápido en dev/demo
existe `scripts/init_db.py`, pero las migraciones son la fuente de verdad.

```bash
# Ejecutar migraciones (usa DATABASE_URL)
alembic upgrade head

# Crear nueva migración desde modelos
alembic revision --autogenerate -m "describe change"
```

## Documentación adicional

- **Arquitectura**: [`context/architecture/layers.md`](context/architecture/layers.md)
- **Threat model**: [`docs/security/threat-model.md`](docs/security/threat-model.md)
- **Runbook**: [`docs/deploy/runbook.md`](docs/deploy/runbook.md)
- **Agentes IA**: [`AGENTS.md`](AGENTS.md)
- **Slides**: [`slides/README.md`](slides/README.md)

## Roadmap

- [x] Dominio: Card, TableSize, MapSpec, AuthZ
- [x] Use cases: CreateCard, GetCard, UpdateCard, DeleteCard, ListCards
- [x] Use cases: ToggleFavorite, ListFavorites
- [x] Adapters: Flask API (cards, favorites, maps)
- [x] Adapters: Gradio UI (completa con autenticación)
- [x] Seguridad: XSS/XXE mitigation en SVG
- [x] Persistencia: PostgreSQL repos con Alembic migrations
- [x] Autenticación: Login/Logout con sesiones PostgreSQL
- [x] Registro: Nueva creación de cuenta con política fuerte de contraseña
- [x] Perfil: Edición de nombre/email + cambio de contraseña
- [ ] Deploy: Cloud (Render/Railway)
- [ ] E2E: Tests completos Flask ↔ Gradio

## Licencia

Pendiente de definir.
