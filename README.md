# MESBG Scenario Card Generator

Scenario Builder es un gestor de escenarios para wargames (Juego de estrategia de guerra en miniatura) con el fin de que un usuario puede crear, ver y editar escenarios. En él, el usuario despliega los datos del escenario a realizar con el fin de que luego se visualice físicamente mediante SVG. A través de ahí, el usuario puede decidir si se lo queda para sí mismo, decide ponerlo en público o querer compartirlo con unos usuarios específicos. A pesar de que ahora mismo está pensado exclusivamente para MESBG (Middle Earth Strategy Battle Game), El objetivo de Scenario Builder está en permitir que un usuario pueda jugar una partida de su wargame con las reglas y datos que serán fiscalizados en la aplicación en cuestión.

> **Arquitectura limpia** con TDD + Security by Design. Ver [`AGENTS.md`](AGENTS.md) y [`context/`](context/) para reglas de desarrollo.

---

## 📋 Tabla de contenidos

- [Resumen rápido](#resumen-rápido)
- [Funcionalidades clave](#funcionalidades-clave)
- [Estado del proyecto](#estado-del-proyecto)
- [Stack técnico](#stack-técnico)
- [Instalación y configuración](#instalación-y-configuración)
- [Testing](#testing)
- [Arquitectura](#arquitectura)
- [API REST](#api-rest)
- [Seguridad](#seguridad)
- [Desarrollo local](#desarrollo-local)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Roadmap](#roadmap)

---

## Resumen rápido

Scenario Builder genera escenarios reproducibles para wargames con salida en SVG, ajustados al tamaño real de mesa del jugador. El flujo base es: eliges parámetros (tamaño de mesa, modo de juego, restricciones), la aplicación valida reglas de dominio (points, deployment zones, constraints) y genera un mapa vectorial listo para visualizar o imprimir a escala real.

**¿Por qué SVG?** Permite renderizar elementos vectoriales escalables para imprimir a tamaño real sin pérdida de calidad. Cada escenario incluye:
- **Dimensiones exactas** con cotas (acotaciones) en cm/in/ft
- **Layout de despliegue** con zonas de entrada para cada ejército
- **Elementos de escenografía** (terreno, fortificaciones, obstáculos)
- **Orientación cardinal** con brújula para determinar direcciones

El sistema incluye control de visibilidad granular (privado/compartido/público), gestión de favoritos, autenticación completa con perfiles editables, y una arquitectura preparada para escalar a múltiples sistemas de wargames.

## Funcionalidades clave

### 🎲 Gestión de escenarios

- **Creación determinista**: Cada escenario tiene un `seed` numérico que garantiza reproducibilidad. Dos usuarios con el mismo seed obtienen el mismo mapa.
- **Edición flexible**: Modifica deployment zones, objetivos, twists y constraints sin perder el seed original.
- **Clonación**: Duplica escenarios existentes con nuevo seed o manteniendo el original.

### 🗺️ Renderizado SVG avanzado

- **Escala ajustable**: Convierte dimensiones de mesa entre cm, inches y feet con precisión de wargamer (1in=2.5cm, 1ft=30cm).
- **Elementos tácticos**: Cotas en bordes del mapa, brújula cardinal, leyenda de zonas.
- **Seguridad**: Hardening contra XSS/XXE con `defusedxml` y allowlist de tags.

### 🔒 Control de visibilidad

- **Privado**: Solo el creador puede ver y editar.
- **Compartido**: Lista allowlist de usuarios específicos.
- **Público**: Visible para todos los usuarios autenticados.

### ⭐ Sistema de favoritos

- Guarda escenarios de otros usuarios para acceso rápido.
- Toggle instantáneo con `POST /favorites/<card_id>/toggle`.

### 👤 Autenticación completa

- Registro con validación de username único y email único.
- Login con lockout automático (3 intentos fallidos → 1 hora bloqueado).
- Perfil editable (nombre, email, contraseña).
- Sesiones seguras con CSRF tokens.

## Estado del proyecto

✅ **Funcional** — 3064+ tests pasando con DB, 1972 unit tests, 11 Gradio smoke tests  
✅ **Quality gates** — ruff, black, mypy, bandit: **all passing** en src/ y tests/  
🏗️ **Adaptadores**: Flask API + Gradio UI con composition root  
🔒 **Seguridad**: XSS/XXE en SVG, anti-IDOR en AuthZ, password policy fuerte, session lockout  
📐 **Arquitectura**: Clean Architecture (domain → application → infrastructure → adapters)  
🗄️ **Persistencia**: PostgreSQL con Alembic migrations + in-memory stores para desarrollo

**Cobertura de tests**: Domain **100%**, Application **99%** (exceeds 80% target), estrategia 60/30/10 (unit/integration/e2e)

**Code quality**: `ruff` 0 errors, `black` compliant, `mypy` strict (205 src/ + 160 test/ files, 0 issues), `bandit` SAST clean

## Stack técnico

### Backend

- **Python 3.11+**: Type hints y pattern matching
- **Flask 2.x+**: API REST con blueprints modulares
- **PostgreSQL 14+**: Base de datos relacional con schemas de usuarios, cards, favoritos, sesiones
- **Alembic**: Migrations versionadas con rollback

### Frontend / UI

- **Gradio 4.x**: Interfaz web declarativa para formularios de creación/edición, galería de escenarios, perfil de usuario y preview SVG en tiempo real

### Testing & Seguridad

- **pytest**: Framework de testing con fixtures y parametrización
- **pytest-cov**: Reportes de cobertura HTML
- **defusedxml**: Parsing seguro XML/SVG para prevenir XXE
- **PBKDF2-HMAC-SHA256**: Hashing de contraseñas (600k iteraciones)
- **secrets**: Generación de tokens CSRF y session IDs

### DevOps

- **Docker + Docker Compose**: Contenedorización multi-stage
- **ruff**: Linting ultrarápido
- **GitHub Actions** (planeado): CI/CD con tests automáticos

## Instalación y configuración

### Requisitos previos

- Python 3.11+ (tested: 3.11.9)
- PostgreSQL 14+ (opcional para dev, requerido en producción)
- Git

### Instalación

```bash
# Clonar y activar entorno
git clone https://github.com/JFRP-89/ScenarioBuilder.git
cd ScenarioBuilder
python -3.11 -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Variables de entorno (.env)

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/scenariobuilder
DATABASE_URL_TEST=postgresql://user:password@localhost:5432/test_scenariobuilder
```

### Validar instalación

```bash
# Tests
pytest tests/unit tests/integration -q

# Code quality gates (all must pass)
ruff check src tests                    # PEP8 + security
black --check src tests                # Code formatting
mypy src --ignore-missing-imports      # Type safety
bandit -r src/domain -q                # Security (domain: 0 issues required)
```

### Ejecutar la aplicación

#### Opción 1: App combinada con Uvicorn (desarrollo local)

Ejecuta Flask API + Gradio UI en un solo proceso:

```powershell
# Windows (PowerShell)
$env:PYTHONPATH = "src"; python -c "import uvicorn; from adapters.combined_app import create_combined_app; uvicorn.run(create_combined_app(), host='127.0.0.1', port=8000)"

# Linux/Mac (bash)
PYTHONPATH=src python -c "import uvicorn; from adapters.combined_app import create_combined_app; uvicorn.run(create_combined_app(), host='127.0.0.1', port=8000)"
```

Accesos:
- `http://localhost:8000/sb/` → Gradio UI
- `http://localhost:8000/auth/*` → Autenticación
- `http://localhost:8000/cards` → API Cards
- `http://localhost:8000/health` → Health check

#### Opción 2: Docker Compose (stack completo con PostgreSQL)

Configura primero el archivo `.env` con las variables necesarias (ver sección anterior), luego:

```bash
docker compose up
```

Esto levanta:
- **Web**: App combinada (Flask + Gradio) en puerto 8000
- **PostgreSQL**: Base de datos en puerto 5432
- **Migraciones**: Se ejecutan automáticamente al iniciar

Accesos:
- `http://localhost:8000/sb/` → Gradio UI
- `http://localhost:8000/auth/*` → Autenticación
- `http://localhost:8000/cards` → API Cards
- `http://localhost:8000/health` → Health check

### Migraciones

```bash
alembic revision --autogenerate -m "Descripción"
alembic upgrade head
alembic downgrade -1
```

## Testing

Estrategia **60/30/10** (60% unit, 30% integration, 10% e2e) con cobertura verificada: **Domain 100%**, **Application 99%**.

**Validación actual**: 3064+ tests passing, 1972 unit tests passing, 11 Gradio smoke tests passing.

### Perfiles

#### Profile A — local-unit (sin DB)

```bash
pytest tests/unit -q                   # 1972 unit tests
pytest --cov=src --cov-report=html    # Reporte en htmlcov/index.html
```

#### Profile B — with-db (con PostgreSQL)

```bash
# Set environment variables
export DATABASE_URL_TEST=postgresql://user:pass@localhost:5432/test_scenariobuilder
export RUN_DB_TESTS=1

# Run full suite with DB
pytest tests/unit tests/integration -q  # 3064+ tests with database
```

### Comandos útiles

```bash
pytest -x                              # Detener en primer fallo
pytest -k "create"                     # Tests que matchean patrón
pytest --lf                            # Re-ejecutar solo tests fallidos
pytest tests/unit/domain/ -v           # Tests de carpeta específica
pytest tests/unit/test_collision.py    # Single file
pytest --cov=src/domain --cov-report=html  # Coverage for specific module
```

## Arquitectura

Clean Architecture (Uncle Bob) con separación estricta de capas y dependency inversion. Flujo: `Adapters → Application → Domain`.

### Capas

```
┌─────────────────────────────────────────┐
│  Adapters (HTTP/UI)                     │  ← Frameworks
│  Flask blueprints, Gradio handlers      │
├─────────────────────────────────────────┤
│  Application (Use Cases)                │  ← Orquestación
│  CreateCard, UpdateCard, GetCardDetail  │
├─────────────────────────────────────────┤
│  Infrastructure (Implementación)        │  ← Tecnología
│  Repos, Auth service, SVG renderer      │
├─────────────────────────────────────────┤
│  Domain (Reglas puras)                  │  ← Negocio
│  Card, Constraints, Scoring, AuthZ      │
└─────────────────────────────────────────┘
```

### 1. Domain (Reglas de negocio)

- Zero dependencias externas (solo stdlib)
- 100% cobertura de tests
- Validación inline (`ValidationError`)
- Módulos: `card/`, `scoring/`, `authz/`, `errors.py`

### 2. Application (Casos de uso)

- Orquesta domain + ports (interfaces)
- DTOs para input/output
- `.execute()` methods
- Importa `domain/`, NO `infrastructure/`
- Módulos: `use_cases/`, `ports/`, `dtos/`

### 3. Infrastructure (Implementaciones)

- Implementa ports con tecnología específica
- PostgreSQL repos, in-memory stores, auth, rendering
- Composition root (`bootstrap.py`)
- Módulos: `persistence/`, `auth/`, `rendering/`, `bootstrap.py`

### 4. Adapters (Frameworks)

- Expone use cases vía HTTP (Flask) o UI (Gradio)
- Solo mapeo, cero lógica de negocio
- CSRF tokens, headers, status codes
- Módulos: `http_flask/`, `ui_gradio/`

### Política de imports

```python
# ✅ Permitido
# domain/ → (nada)
# application/ → domain/
# infrastructure/ → domain/, application/
# adapters/ → domain/, application/, infrastructure/

# ❌ Prohibido
# domain/ → application/
# application/ → infrastructure/
```

Ver [`context/architecture/layers.md`](context/architecture/layers.md) para detalles.

## API REST

**Base URL**: `http://localhost:5000` (dev) o `http://localhost:8000` (Docker)

### Autenticación

- `POST /auth/register` — Registra usuario nuevo (username/email únicos)
  - Request: `{"username", "email", "password", "full_name"}`
  - Response 201: `{"message", "username"}`
  - Validaciones: username 3-30 chars, email válido, password 8+ chars con mayúscula/número/especial

- `POST /auth/login` — Inicia sesión (lockout tras 3 fallos → 1h)
  - Request: `{"username", "password"}`
  - Response 200: `{"message", "session_id", "csrf_token"}`

- `GET /auth/me` — Perfil del usuario autenticado
  - Headers: `X-Session-Id`, `X-Actor-Id`
  - Response 200: `{"username", "email", "full_name", "created_at"}`

- `PUT /auth/profile` — Actualiza perfil
  - Headers: `X-Session-Id`, `X-Actor-Id`, `X-CSRF-Token`
  - Request: `{"full_name"?, "email"?, "password"?}` (campos opcionales)

### Escenarios (Cards)

- `POST /cards` — Crea nuevo escenario
  - Headers: `X-Actor-Id`, `X-CSRF-Token`
  - Request: `{"seed", "table_width_cm", "table_depth_cm", "game_mode", "constraints", "visibility"}`
  - Response 201: `{"card_id", "seed", "map_url"}`

- `GET /cards/<card_id>` — Detalle de escenario (requiere permisos de lectura)
  - Headers: `X-Actor-Id`
  - Response 200: `{"card_id", "seed", "spec", "layout", "visibility", "owner_id", "created_at"}`
  - Errores: 404 (no existe), 403 (sin permisos)

- `PUT /cards/<card_id>` — Actualiza escenario (solo owner)
  - Headers: `X-Actor-Id`, `X-CSRF-Token`
  - Request: `{"visibility"?, "constraints"?}`

- `GET /cards/<card_id>/map.svg` — Descarga SVG
  - Query: `display_units=cm|in|ft` (default: cm)
  - Response 200: `image/svg+xml`

### Favoritos

- `POST /favorites/<card_id>/toggle` — Añade/quita favorito
  - Headers: `X-Actor-Id`, `X-CSRF-Token`
  - Response 200: `{"favorited": bool, "favorites_count": int}`

- `GET /favorites` — Lista favoritos del usuario
  - Headers: `X-Actor-Id`
  - Response 200: `{"favorites": [{"card_id", "seed", "owner_id", "created_at"}]}`

### Health

- `GET /health` — Verifica que API está viva (sin auth)
  - Response 200: `{"status": "healthy", "timestamp"}`

## Seguridad

### Autenticación

- **Password hashing**: PBKDF2-HMAC-SHA256 (600k iteraciones) + salt 16 bytes
- **Password policy**: 8+ chars, mayúscula, número, especial
- **Lockout**: 3 intentos → 1 hora bloqueado

### Autorización (AuthZ)

- **Modelo deny-by-default**: Negar todo, permitir explícitamente
- **Permisos**: read, update, delete, share
- **Visibilidad**: private (solo owner), shared (owner + allowlist), public (owner + todos)
- **Anti-IDOR**: Verificación de permisos antes de retornar datos

### Protección contra ataques

- **CSRF**: Todos los POST/PUT/DELETE requieren `X-CSRF-Token`
- **XSS en SVG**: Allowlist de tags, escape de atributos, CSP header, Content-Type forzado
- **XXE**: `defusedxml` en lugar de stdlib (DTD deshabilitados)
- **SQL Injection**: Parametrización en todas las queries

### SAST

```bash
bandit -r src/ -f json -o reports/bandit_all.json
bandit -r src/domain/ -f json -o reports/bandit_domain.json  # Debe ser 0 issues
```

### Gestión de secretos

Variables sensibles (NUNCA commitear):
- `DATABASE_URL`

Usar `.env` local (excluido en `.gitignore`) o variables de entorno en producción. Rotar credenciales cada 90 días.

Ver [`context/security/`](context/security/) para documentación completa.

## Desarrollo local

### Workflow TDD (RED → GREEN → REFACTOR)

```bash
# RED: Test que falla
pytest tests/unit/domain/test_nueva_regla.py -v

# GREEN: Implementar mínimo código
pytest tests/unit/domain/test_nueva_regla.py -v

# REFACTOR: Mejorar sin romper
pytest tests/unit tests/integration -q
```

### Convenciones

- **Estilo**: PEP 8 (ruff), type hints, docstrings (Google format)
- **Naming**: PascalCase (clases), snake_case (funciones), UPPER_SNAKE_CASE (constantes)
- **Imports**: stdlib → third-party → project (absolutos)

### Debugging

```json
// .vscode/launch.json
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
    }
  ]
}
```

## Estructura del proyecto

```
ScenarioBuilder/
├── src/
│   ├── domain/              # Reglas puras (Card, Scoring, AuthZ)
│   ├── application/         # Use cases + ports + DTOs
│   ├── infrastructure/      # Repos, auth, rendering, bootstrap
│   └── adapters/            # Flask (HTTP) + Gradio (UI)
├── tests/
│   ├── unit/                # 60% (domain 100%, application 80%)
│   ├── integration/         # 30% (HTTP e2e, DB real)
│   └── e2e/                 # 10% (smoke tests)
├── content/mesbg/           # Datos de dominio (constraints, deployments, objectives)
├── context/                 # Documentación para agentes (arquitectura, calidad, seguridad)
├── docs/                    # Documentación técnica
├── docker-compose.yml       # Stack completo (web + db)
├── Dockerfile               # Imagen de producción
├── requirements.txt         # Dependencias producción
├── requirements-dev.txt     # Dependencias desarrollo
├── pyproject.toml           # Configuración (ruff, pytest)
├── AGENTS.md                # Reglas para agentes IA
└── README.md                # Este archivo
```

## Roadmap

### 🚀 Próximos releases

**v0.2.0 — Mejoras de experiencia y expansión**

- **Mejoras de UX (wizard, presets de mesa)**: Con el objetivo de que un usuario normal no tenga que estar escribiendo constantemente las coordenadas, se implementará tanto una mejora en el UX como en el hecho de introducir la característica de crear figuras.

- **Export (PDF/imagen) y assets imprimibles**: Se implementará esta característica para que puedan guardarlo en la máquina sin necesidad de estar conectado a Scenario Builder.

- **Expandirse a más allá de la Tierra Media**: Por mucho que MESBG (Middle Earth Strategy Battle Game) sea un muy buen juego como un wargame, como se comentó antes, más adelante se tiene pensado escalarlo a otros juegos, añadiendo más filtros relacionados con el wargame que jugar para que un usuario no se vea forzado a ver escenarios de juegos a los que realmente no les interesa ver.

---

## 📄 Licencia

Pendiente de definir. Todos los derechos reservados (por ahora).

---

## 📞 Contacto

- **Autor**: Juan Francisco (JFRP-89)
- **Repositorio**: [github.com/JFRP-89/ScenarioBuilder](https://github.com/JFRP-89/ScenarioBuilder)
- **Issues**: [github.com/JFRP-89/ScenarioBuilder/issues](https://github.com/JFRP-89/ScenarioBuilder/issues)

**¿Bugs de seguridad?** NO abrir issue público. Contactar directamente al mantenedor.

---

Consulta documentación adicional en [`context/`](context/) y [`docs/`](docs/).