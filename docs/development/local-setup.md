# Guía de Desarrollo Local

## Requisitos previos

- **Python 3.11+** (tested: 3.11.9) — requerido por type hints y pattern matching
- **Git** — control de versiones
- **PostgreSQL 14+** — opcional en dev (fallback a in-memory). Requerido para `RUN_DB_TESTS=1`
- **Docker + Docker Compose** — opcional para stack completo

---

## Setup inicial

### 1. Clonar repositorio

```bash
git clone https://github.com/JFRP-89/ScenarioBuilder.git
cd ScenarioBuilder
```

### 2. Crear entorno virtual

```bash
# Windows
python -3.11 -m venv venv311
venv311\Scripts\activate

# Linux/Mac
python3.11 -m venv venv311
source venv311/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt        # Producción
pip install -r requirements-dev.txt    # Desarrollo (pytest, ruff, mypy, bandit)
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env si se usa PostgreSQL
```

Sin PostgreSQL, la app funciona con repositorios in-memory (datos se pierden
al reiniciar).

### 5. Verificar instalación

```bash
# Tests
pytest tests/unit -q                    # 1972 unit tests (no DB required)

# Code quality gates (todos deben pasar)
ruff check src tests                    # PEP8 + security → 0 errors
black --check src tests                 # Code formatting
mypy src --ignore-missing-imports       # Type safety (205 files, 0 issues)
bandit -r src/domain -q                 # Security (domain: 0 issues required)

# Con PostgreSQL (opcional)
export RUN_DB_TESTS=1
export DATABASE_URL_TEST=postgresql://user:pass@localhost:5432/test_sb
pytest tests/unit tests/integration -q  # 3064+ tests con DB
```

---

## Ejecutar la aplicación

### Opción 1: Uvicorn (recomendada para dev)

```powershell
# Windows PowerShell
$env:PYTHONPATH = "src"
python -c "import uvicorn; from adapters.combined_app import create_combined_app; uvicorn.run(create_combined_app(), host='127.0.0.1', port=8000)"
```

```bash
# Linux/Mac
PYTHONPATH=src python -c "
import uvicorn
from adapters.combined_app import create_combined_app
uvicorn.run(create_combined_app(), host='127.0.0.1', port=8000)
"
```

Accesos:
- **Gradio UI**: http://localhost:8000/sb/
- **API REST**: http://localhost:8000/cards
- **Auth**: http://localhost:8000/auth/login
- **Health**: http://localhost:8000/health

### Opción 2: Docker Compose

```bash
docker compose up --build
```

Ver [docs/deploy/runbook.md](../deploy/runbook.md) para detalles.

### Opción 3: Scripts de conveniencia

```powershell
# Windows
.\scripts\run_ui_local.ps1    # Solo Gradio UI
.\scripts\run_api_local.ps1   # Solo Flask API
```

```bash
# Linux/Mac
./scripts/run_ui_local.sh
./scripts/run_api_local.sh
```

---

## Workflow TDD

Todo el desarrollo sigue el ciclo **RED → GREEN → REFACTOR**:

```bash
# 1. RED — Escribir test que falla
pytest tests/unit/domain/test_nueva_feature.py -v
# ❌ FAILED

# 2. GREEN — Implementar el mínimo código
pytest tests/unit/domain/test_nueva_feature.py -v
# ✅ PASSED

# 3. REFACTOR — Mejorar sin romper tests
pytest tests/unit tests/integration -q
# ✅ All passed
```

**Regla**: Si el prompt dice "solo tests" → NO tocar `src/`.

---

## Quality Gates (todos obligatorios antes de PR)

### Ruff (PEP8 + seguridad) — 0 errors

```bash
ruff check src tests                    # Verificar
ruff check src tests --fix              # Auto-fix
```

Configurado en `pyproject.toml`: line-length 88, reglas F, E, W, C90, B, SIM, RUF, I (import sorting).
Estado: **All checks passed** en src/ y tests/

### Black (code formatting) — must be compliant

```bash
black --check src tests                 # Verificar
black src tests                         # Auto-format
```

Estado: **All files compliant** (218 src/ + 172 test/ files)

### Mypy (type safety) — 0 errors

```bash
mypy src --ignore-missing-imports       # Verificar source
mypy tests --ignore-missing-imports     # Verificar tests
```

Configurado en `pyproject.toml`: `check_untyped_defs = true`, `no_implicit_optional = true`.
Estado: **0 issues** en 205 src/ files y 160 test/ files

### Bandit (SAST) — domain: 0 issues

```bash
bandit -r src/ -f json -o reports/bandit_all.json
bandit -r src/domain/ -f json -o reports/bandit_domain.json  # Debe ser 0
```

---

## Testing

### Ejecutar todos los tests

```bash
pytest -q                          # Rápido
pytest -v                          # Verbose
pytest -x                          # Parar en primer fallo
pytest --lf                        # Re-ejecutar fallidos
```

### Por categoría

```bash
pytest tests/unit -q               # Unit (60%)
pytest tests/integration -q        # Integration (30%)
pytest tests/e2e -q                # E2E (10%)
```

### Con cobertura

```bash
pytest --cov=src --cov-report=html
# Abrir htmlcov/index.html en el navegador
```

### Tests específicos

```bash
pytest -k "create_card"                              # Patrón
pytest tests/unit/domain/test_card_model.py -v       # Archivo
pytest tests/unit/domain/test_card_model.py::TestCardCreation::test_valid  # Test
```

Ver [docs/testing/strategy.md](../testing/strategy.md) para la estrategia completa.

---

## Estructura de archivos clave

```
src/
├── domain/              # NO tocar sin test primero
│   ├── cards/           # Card, generator, scoring, constraints
│   ├── maps/            # TableSize, MapSpec, collision
│   ├── security/        # Visibility, can_read, can_write
│   ├── errors.py        # ValidationError, NotFoundError, ForbiddenError
│   ├── validation.py    # validate_non_empty_str
│   └── seed.py          # get_rng, normalize_seed
│
├── application/
│   ├── ports/           # Protocol interfaces
│   └── use_cases/       # Request DTO → execute → Response DTO
│
├── infrastructure/
│   ├── bootstrap.py     # ⭐ Composition root
│   ├── repositories/    # In-memory + PostgreSQL
│   ├── generators/      # UUID, seed, deterministic
│   ├── maps/            # SVG renderer
│   ├── auth/            # Auth service, sessions, users
│   └── db/              # SQLAlchemy models
│
└── adapters/
    ├── http_flask/      # API REST (blueprints)
    ├── ui_gradio/       # Gradio UI (facades + wiring)
    └── combined_app.py  # FastAPI wrapper
```

---

## Convenciones de código

### Estilo

- **PEP 8** via ruff (line-length 88)
- **Type hints** en todas las funciones
- **Docstrings** en formato Google
- **Imports** absolutos desde paquete (`from domain.cards.card import Card`)

### Naming

| Tipo | Convención | Ejemplo |
|------|-----------|---------|
| Clases | PascalCase | `Card`, `TableSize`, `SaveCard` |
| Funciones | snake_case | `generate_card()`, `can_read()` |
| Constantes | UPPER_SNAKE | `MAX_SEED`, `CM_PER_INCH` |
| Módulos privados | prefijo `_` | `_geometry.py`, `_form_state.py` |
| Tests | `test_<action>_<scenario>` | `test_create_card_with_valid_seed` |

### Imports

```python
# 1. stdlib
import os
from datetime import datetime

# 2. third-party
from flask import Blueprint
import gradio as gr

# 3. project
from domain.cards.card import Card
from application.ports.repositories import CardRepository
```

**Prohibido**: `from src.domain...` (usar imports absolutos desde paquete).

---

## Debugging

### VS Code launch.json

```json
{
  "configurations": [
    {
      "name": "Flask API",
      "type": "python",
      "module": "flask",
      "args": ["--app", "src.adapters.http_flask.app", "run", "--debug"]
    },
    {
      "name": "Pytest current file",
      "type": "python",
      "module": "pytest",
      "args": ["${file}", "-v"]
    },
    {
      "name": "Combined App (Uvicorn)",
      "type": "python",
      "module": "uvicorn",
      "args": [
        "adapters.combined_app:create_combined_app",
        "--factory",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
      ],
      "env": {"PYTHONPATH": "${workspaceFolder}/src"}
    }
  ]
}
```

---

## Documentación para agentes

La carpeta `context/` contiene documentación estructurada para agentes IA
que trabajan en el proyecto. Ver [AGENTS.md](../../AGENTS.md) para el índice
completo.

Las reglas globales más importantes:
1. Nada de lógica de negocio en adapters.
2. `domain/` no importa de ninguna otra capa.
3. TDD: RED → GREEN → REFACTOR.
4. Composition root: solo vía `build_services()`.
5. Prohibido `src.` en imports.
