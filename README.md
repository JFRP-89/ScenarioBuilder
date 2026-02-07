# MESBG Scenario Card Generator

Generador de cartas de escenario para Middle-earth Strategy Battle Game (MESBG) con modos `casual`, `narrative` y `matched`.
Incluye generación determinista por `seed`, renderizado de **board layouts en SVG** con seguridad XSS/XXE, y gestión de favoritos.

> **Arquitectura limpia** con TDD + Security by Design. Ver [`AGENTS.md`](AGENTS.md) y [`context/`](context/) para reglas de desarrollo.

## Estado del proyecto

✅ **Funcional** — 412 tests pasando  
🏗️ **Adaptadores**: Flask API modernizada + Gradio UI con composition root  
🔒 **Seguridad**: XSS/XXE mitigation en SVG, anti-IDOR en AuthZ  
📐 **Arquitectura**: Clean Architecture (domain → application → infrastructure → adapters)

## Stack técnico

- **Python 3.11+** (type hints con `|`, dataclasses)
- **Flask 2.x+** (API REST con Blueprints)
- **Gradio 4.x** (UI interactiva)
- **PostgreSQL** (persistencia, pendiente)
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
pytest -q                     # Todos (412 tests)
pytest tests/unit -q          # Solo unitarios (rápido)
pytest -q --cov=src --cov-report=term-missing  # Con coverage

# Linting
ruff check .
```

### Docker

```bash
docker compose up

# API: http://localhost:8000
# UI:  http://localhost:7860
```

## Estructura del proyecto

```
ScenarioBuilder/
├── src/
│   ├── domain/              # Reglas de negocio puras (no depende de nada)
│   │   ├── cards/           # Card, Visibility, GameMode
│   │   ├── maps/            # TableSize, MapSpec
│   │   └── security/        # Authorization (anti-IDOR)
│   ├── application/         # Casos de uso + ports (depende de domain)
│   │   ├── use_cases/       # CreateCard, ToggleFavorite, etc.
│   │   └── ports/           # Interfaces (repos, generators)
│   ├── infrastructure/      # Implementaciones (depende de application)
│   │   ├── bootstrap.py     # Composition root (build_services)
│   │   ├── repositories/    # In-memory repos (CardRepo, FavoritesRepo)
│   │   ├── generators/      # ID/Seed generators
│   │   └── maps/            # SVG renderers (con XSS/XXE mitigation)
│   └── adapters/            # HTTP/UI (depende de infrastructure)
│       ├── http_flask/      # Flask API (cards, favorites, maps)
│       └── ui_gradio/       # Gradio UI (sin HTTP en import/build)
├── content/                 # JSON editable (constraints, objectives, etc.)
├── tests/                   # TDD: 60% unit, 30% integration, 10% e2e
│   ├── unit/                # Tests de dominio y lógica pura
│   ├── integration/         # Tests de adapters + repos
│   └── e2e/                 # Tests end-to-end (placeholder)
├── context/                 # Conocimiento para IA (arquitectura, calidad, security)
│   ├── architecture/        # Layers, import policy, error model
│   ├── quality/             # TDD, coverage, SOLID
│   ├── security/            # Security by design, anti-IDOR, input validation
│   └── workflow/            # Centaur mode, prompting
├── docs/                    # Documentación de evaluación
└── AGENTS.md                # Índice de reglas globales + punteros a context/
```

## API Flask — Endpoints

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
- [x] Adapters: Gradio UI (smoke tests)
- [x] Seguridad: XSS/XXE mitigation en SVG
- [ ] Persistencia: PostgreSQL repos
- [ ] Deploy: Cloud (Render/Railway)
- [ ] E2E: Tests completos Flask ↔ Gradio

## Licencia

Pendiente de definir.
