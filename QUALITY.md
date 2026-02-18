# QUALITY.md — ScenarioBuilder

> **Última actualización**: febrero 2026 · branch `ui/alpha.0.8`

---

## 1. Propósito y alcance

### ¿Qué significa "calidad" en este proyecto?

Calidad = código correcto, seguro, mantenible y verificable de forma automatizada.
Se sustenta en cuatro pilares:

1. **Corrección** — tests que prueban reglas de negocio, integración con DB y flujo E2E.
2. **Seguridad** — deny-by-default, anti-IDOR, PBKDF2, validación allowlist, defusedxml.
3. **Mantenibilidad** — arquitectura por capas, facade pattern, imports unidireccionales.
4. **Automatización** — CI con quality gates obligatorios (lint, cobertura, contrato kwargs).

### ¿A quién va dirigido?

- Desarrolladores del equipo (día a día).
- Reviewers de Pull Requests (checklist de aceptación).
- Contributors externos (mapa rápido de herramientas y comandos).

### ¿Qué cubre y qué no?

| Cubre | No cubre |
|---|---|
| Código fuente Python (`src/`) | Frontend estático (no hay) |
| Tests (`tests/`) | Pruebas de rendimiento bajo carga |
| CI/CD (GitHub Actions) | Despliegue a producción (infra cloud) |
| Seguridad a nivel de código | Auditoría de red / firewalls |
| Docker local / compose | Orquestación Kubernetes |

---

## 2. Resumen ejecutivo de calidad

| Aspecto | Estado | Herramienta | Cómo se ejecuta | Notas |
|---|---|---|---|---|
| **Formatter** | ✅ Verificado | Black 24.8.0 | `black --check src tests` | Line length 88, CI gate |
| **Lint** | ✅ Verificado | Ruff 0.5.6 | `ruff check .` | Reglas: F, E, W, C90, B, SIM, C4, RUF, I |
| **Type-check** | ✅ Verificado | mypy 1.8.0 | `mypy src` | `check_untyped_defs=true`, `ignore_missing_imports=true`. No gate en CI (local/dev) |
| **Tests unitarios** | ✅ Verificado | pytest 8.2.0 | `pytest tests/unit -q` | ~1 731 tests, baseline 2 551 passed (unit+integ) |
| **Tests integración** | ✅ Verificado | pytest + PostgreSQL 16 | `pytest tests/integration -q` | ~883 tests, requiere `RUN_DB_TESTS=1` para DB |
| **Tests E2E** | ✅ Verificado | Playwright 1.49.0 | `pytest -m e2e` | ~20 tests, manual dispatch en CI |
| **Cobertura** | ✅ Verificado | pytest-cov 5.0.0 | `pytest --cov=src` | Política: domain 100%, application ≥80% |
| **SAST** | ⚠️ Parcial | Bandit 1.7.6 | `bandit -r src` | Configurado en `pyproject.toml`, no en CI gate |
| **Complejidad** | ⚠️ Parcial | Radon 6.0.1 | `radon cc src -a` | Disponible via `make complexity`, no en CI gate |
| **Dead code** | ⚠️ Parcial | Vulture 2.10 | `vulture src --min-confidence 80` | Disponible via `make deadcode`, no en CI gate |
| **Duplicación** | ⚠️ Parcial | Pylint 3.0.3 | `pylint --disable=all --enable=duplicate-code src` | Disponible via `make duplication`, no en CI gate |
| **Dependencias** | ❌ No encontrado | — | — | No hay Dependabot ni Renovate configurado |
| **CI/CD** | ✅ Verificado | GitHub Actions | `.github/workflows/ci.yml` | 5 jobs: lint → unit → integration → docker → manual |
| **Observabilidad** | ⚠️ Parcial | `logging` stdlib | — | Solo en infrastructure/adapters (6 módulos). Sin métricas ni trazas |
| **Contrato kwargs** | ✅ Verificado | `_kwargs.py` + test | `STRICT_KWARGS_CONTRACT=1` en CI | Golden test para firma `wire_events` ↔ `build_create_page` |

---

## 3. Estándares de código y estilo

### 3.1 Formatter y linter

| Herramienta | Config | Reglas clave |
|---|---|---|
| **Black** | Implícito (line-length 88) | Formato determinístico, CI bloquea si hay diff |
| **Ruff** | `pyproject.toml` → `[tool.ruff]` | F (Pyflakes), E/W (pycodestyle), C90 (McCabe), B (Bugbear), SIM, C4, RUF, I (isort) |
| **isort** | Via Ruff `I` | `known-first-party = ["src"]` |

### 3.2 Convenciones de naming

- **Módulos**: `snake_case.py` (ej: `wire_detail.py`, `card_repository.py`).
- **Clases**: `PascalCase` (ej: `ValidationError`, `SvgMapRenderer`).
- **Funciones/métodos**: `snake_case` (ej: `build_create_page`, `kwargs_for_call`).
- **Constantes**: `UPPER_SNAKE_CASE` (ej: `EXPLICIT_OVERRIDES`, `PAGE_HOME`).
- **Módulos internos** (no públicos): prefijo `_` (ej: `_kwargs.py`, `_render.py`, `_converters.py`).
- **Paquetes internos** (facade split): prefijo `_` en carpeta (ej: `_deployment/`, `_scenography/`).

### 3.3 Organización de archivos

- Imports absolutos desde el paquete (nunca `src.`).
- `from __future__ import annotations` en todos los archivos.
- Docstrings: módulo (propósito), funciones públicas (params + returns).
- Comentarios de sección con `# ── Título ──` para separar bloques dentro de funciones largas.

### 3.4 Reglas de complejidad

| Herramienta | Métrica | Límite configurado |
|---|---|---|
| Ruff `C90` | Complejidad ciclomática | Implícito (default 10) |
| Pylint | `max-locals` | 15 |
| Pylint | `max-branches` | 12 |
| Pylint | `max-statements` | 50 |
| Radon | Complejidad ciclomática | Reporte manual (`make complexity`) |

### 3.5 Política de duplicación y dead code

- **Duplicación**: `make duplication` ejecuta Pylint `duplicate-code`. No hay gate en CI.
- **Dead code**: `make deadcode` ejecuta Vulture (confianza ≥80%). No hay gate en CI.
- **Magic numbers**: no hay regla explícita configurada. `TODO:` evaluar habilitar Ruff `PLR2004`.

---

## 4. Arquitectura y diseño

### 4.1 Capas del sistema

```
┌─────────────────────────────────────────────┐
│  adapters/                                  │  Flask HTTP + Gradio UI
│  ├─ http_flask/   (REST API, auth routes)   │  Solo mapeo HTTP/UI + wiring
│  ├─ ui_gradio/    (Gradio multi-page SPA)   │  Sin lógica de negocio
│  └─ combined_app  (ASGI mount FastAPI)      │
├─────────────────────────────────────────────┤
│  infrastructure/                            │  Implementaciones concretas
│  ├─ repositories/  (InMemory, Postgres)     │  + composition root
│  ├─ auth/          (sessions, users)        │  (build_services)
│  ├─ db/            (SQLAlchemy sessions)    │
│  └─ bootstrap.py   (composition root)      │
├─────────────────────────────────────────────┤
│  application/                               │  Use cases + ports
│  ├─ use_cases/     (generate, save, list…)  │  DTOs + .execute()
│  └─ ports/         (interfaces abstractas)  │
├─────────────────────────────────────────────┤
│  domain/                                    │  Reglas puras
│  ├─ cards/         (modelos, scoring, …)    │  Sin dependencias externas
│  ├─ maps/          (spec, table_size)       │
│  └─ security/      (authz, anti-IDOR)      │
└─────────────────────────────────────────────┘
```

### 4.2 Política de imports (unidireccional)

| Capa | Puede importar de |
|---|---|
| `domain/` | Nada (cero dependencias) |
| `application/` | `domain/` |
| `infrastructure/` | `domain/`, `application/` |
| `adapters/` | `application/`, `infrastructure/` (solo composition root), `domain/` (solo tipos) |

Se verifica con test automatizado: `tests/unit/domain/test_domain_imports.py`.

### 4.3 Principios de diseño

- **SOLID** documentado en `context/quality/solid-checklist.md`:
  - SRP: un repo, un generador, un renderer, un use case por clase.
  - OCP: extensión vía nuevos generadores/renderers sin modificar existentes.
  - LSP: implementaciones cumplen el contrato del port.
  - ISP: ports pequeños (7 ficheros de interfaz).
  - DIP: application define ports, infrastructure los implementa.
- **Composition root**: todo el wiring en `infrastructure.bootstrap.build_services()`.
- **Facade pattern**: wire modules <450 LOC, internos en `_paquete/` con tests 1:1.

### 4.4 Inventario de tamaños

| Capa | Archivos | LOC |
|---|---|---|
| `domain/` | 21 | 1 222 |
| `application/` | 31 | 2 680 |
| `infrastructure/` | 35 | 3 269 |
| `adapters/` | 127 | 13 489 |
| **Total `src/`** | **215** | **20 661** |

### 4.5 God Modules — detección y mitigación

Los adapters (65% del código) concentran la complejidad de UI. Mitigaciones aplicadas:

| Módulo | Estado | LOC actual | Acción |
|---|---|---|---|
| `app.py` (Gradio orquestador) | ✅ Mitigado | ~400 | Reducido de 1 142 → 400 vía extracción de páginas |
| `wire_events/__init__.py` | ⚠️ Vigilar | ~456 | Firma de ~130 params; delegación a sub-wirers |
| `create_scenario.py` | ⚠️ Vigilar | ~464 | Builder legítimo; no conviene partir sin motivo |
| Facades `wire_*.py` | ✅ Controlado | 250–450 c/u | Façade pattern + paquetes internos `_*/` |

`TODO:` Ejecutar `radon cc src/adapters -a -nc` periódicamente para detectar funciones con complejidad ciclomática >10.

### 4.6 Antipatrones a evitar

- ❌ Lógica de negocio en adapters (Flask/Gradio solo mapeo HTTP/UI).
- ❌ Imports circulares entre capas.
- ❌ `src.` en imports (usar imports absolutos desde paquete).
- ❌ Instanciar repos/use cases fuera del composition root.
- ❌ God modules >500 LOC sin split en internos.
- ❌ `**kwargs` en firmas de wire functions (preferir keyword-only explícito).

---

## 5. Pruebas y estrategia de testing

### 5.1 Pirámide de testing

| Tipo | Objetivo | Tests | % real | % target |
|---|---|---|---|---|
| **Unit** | Reglas dominio, use cases, wiring aislado | ~1 731 | 66% | 60% |
| **Integration** | DB (Postgres), combined app, auth flows | ~883 | 33% | 30% |
| **E2E** | docker-compose + Playwright | ~20 | 1% | 10% |

Ratio test:source ≈ **1.06:1** (21 972 LOC tests / 20 661 LOC src).

### 5.2 Frameworks y ubicación

| Framework | Ubicación | Propósito |
|---|---|---|
| pytest 8.2.0 | `tests/` | Runner principal |
| pytest-cov 5.0.0 | CI step | Cobertura |
| Playwright 1.49.0 | `tests/e2e/` | Browser automation E2E |

### 5.3 Cobertura — política y enforcement

| Capa | Mínimo requerido | Enforcement |
|---|---|---|
| `domain/` | **100%** | CI gate: `--fail-under=100` |
| `application/` | **80%** | CI gate: `--fail-under=80` |
| `infrastructure/` | Sin gate | Recomendado 80% |
| `adapters/` | Sin gate | Medido pero no bloqueante |

Comando: `pytest tests/unit --cov=src --cov-report=term-missing --cov-report=json`

### 5.4 Qué debe testearse obligatoriamente

- [ ] Todas las reglas de dominio (validación, scoring, constraints, authz).
- [ ] Todos los use cases (`.execute()` con happy path + error path).
- [ ] Endpoints REST (status codes, body, auth guards).
- [ ] Auth flows (login, logout, profile, lockout, session expiry).
- [ ] Contrato `wire_events ↔ build_create_page` (golden contract test).
- [ ] Imports de dominio no violan política de capas.

### 5.5 Patrones de testing observados

- **Fixtures** en `conftest.py`: `load_env` (session-scoped, autouse), `db_enabled()`, `sample_card()`.
- **Dual-profile**: `RUN_DB_TESTS=1` habilita tests PostgreSQL; sin él, solo InMemory.
- **Parametrize**: usado extensivamente en auth validators (27 tests), store (32), service (42).
- **Mocks**: `unittest.mock.patch` para repos/services en unit tests de use cases.
- **Golden contract**: `test_wire_events_contract.py` verifica firma ↔ namespace en CI con `STRICT_KWARGS_CONTRACT=1`.
- **Marker auto-skip**: `@pytest.mark.db` se salta automáticamente si DB no disponible (local-dev).

---

## 6. Automatización de calidad (CI/CD)

### 6.1 Pipelines detectados

| Workflow | Archivo | Trigger | Jobs |
|---|---|---|---|
| **CI** | `.github/workflows/ci.yml` | push `main`, PR → `main` | lint, test-unit, test-integration, docker-build, manual-full-suite, manual-e2e |
| **E2E** | `.github/workflows/e2e.yml` | `workflow_dispatch` | E2E con Playwright + docker-compose |

### 6.2 Quality gates (bloquean merge)

| Gate | Job | Condición |
|---|---|---|
| Ruff lint | `lint` | `ruff check .` sin errores |
| Black format | `lint` | `black --check src tests` sin diff |
| Unit tests | `test-unit` | Todos pasan |
| Domain coverage | `test-unit` | ≥100% |
| Application coverage | `test-unit` | ≥80% |
| Strict kwargs contract | `test-unit` | `STRICT_KWARGS_CONTRACT=1` — 0 extras, 0 missing |
| DB integration tests | `test-integration` | Todos corren (0 skipped) |
| Non-DB integration | `test-integration` | Todos pasan |
| Docker build | `docker-build` | Build exitoso + `docker compose config` válido |

### 6.3 Artefactos generados

| Artefacto | Retención | Job |
|---|---|---|
| `coverage-report` (HTML) | 7 días | test-unit |
| `coverage-report-manual` (HTML) | 7 días | manual-full-suite |

### 6.4 Checklist antes de abrir PR

- [ ] `ruff check .` limpio (0 errores).
- [ ] `black --check src tests` limpio (0 diffs).
- [ ] `pytest tests/unit -q` verde (todos pasan).
- [ ] `pytest tests/integration -q` verde (con `RUN_DB_TESTS=1` si hay cambios DB).
- [ ] Cobertura domain 100%, application ≥80%.
- [ ] CHANGELOG.md actualizado con la entrada correspondiente.
- [ ] Sin imports `src.` ni lógica de negocio en adapters.
- [ ] Facades <450 LOC; si hay un nuevo wire module, tiene tests 1:1 internos.
- [ ] PR template completado (tipo de cambio, SemVer, amenazas).

---

## 7. Seguridad y cumplimiento

### 7.1 Prácticas implementadas

| Práctica | Estado | Detalle |
|---|---|---|
| **Deny-by-default** | ✅ | Authz en `domain/security/authz.py`, anti-IDOR |
| **Hashing de passwords** | ✅ | PBKDF2-HMAC-SHA256, 100 000 iteraciones, salt 32 bytes |
| **Brute-force lockout** | ✅ | 3 intentos fallidos → lockout 1 hora por username |
| **Validación allowlist** | ✅ | Regex con `\Z` (no `$`), username/email/display_name |
| **SVG sanitización** | ✅ | `defusedxml` para parseo seguro de XML/SVG |
| **Error genérico** | ✅ | "Invalid credentials" sin enumerar usuarios |
| **Non-root Docker** | ✅ | `USER appuser` (uid 1000) en Dockerfile |
| **CSRF** | ✅ | Token `sb_csrf` en cookie, verificado en logout |
| **HttpOnly cookies** | ✅ | `sb_session` para sesión de autenticación |

### 7.2 Gestión de secretos

- Variables de entorno vía `.env` (no commiteado; `.env.example` como referencia).
- `SECRET_KEY` en docker-compose.yml con valor placeholder `change-me-in-production`.
- CI usa variables de entorno del runner (no secrets de GitHub).
- `TODO:` Verificar que `.env` está en `.gitignore`.

### 7.3 SAST y análisis de dependencias

| Herramienta | Configurado | En CI | Notas |
|---|---|---|---|
| **Bandit** | ✅ `pyproject.toml` | ❌ No es gate | Disponible via `make security` o `bandit -r src` |
| **CodeQL** | ❌ No encontrado | ❌ | `TODO:` Añadir `.github/workflows/codeql.yml` |
| **Dependabot** | ❌ No encontrado | — | `TODO:` Crear `.github/dependabot.yml` para pip |
| **Renovate** | ❌ No encontrado | — | Alternativa a Dependabot |
| **Snyk** | ⚠️ Instrucción | — | Regla en `.github/instructions/snyk_rules.instructions.md` como guía de Copilot |

### 7.4 Recomendaciones pendientes

- [ ] `TODO:` Añadir Dependabot para actualizaciones automáticas de dependencias pip.
- [ ] `TODO:` Añadir CodeQL workflow para análisis estático de seguridad en PRs.
- [ ] `TODO:` Incluir `bandit -r src` como gate en CI (job lint o separado).
- [ ] `TODO:` Verificar que no se loguean credenciales ni tokens en producción.

---

## 8. Fiabilidad, observabilidad y operación

### 8.1 Logging

- **Librería**: `logging` stdlib de Python.
- **Patrón**: `logger = logging.getLogger(__name__)`.
- **Uso**: exclusivamente en `infrastructure/` y `adapters/` (6 módulos).
  - `infrastructure/bootstrap.py`, `infrastructure/db/session.py`
  - `infrastructure/auth/session_store.py`, `infrastructure/auth/postgres_session_store.py`, `infrastructure/auth/auth_service.py`
  - `adapters/http_flask/middleware.py`
- **No se usa en `domain/` ni `application/`** — correcto per clean architecture.
- `TODO:` Definir niveles de log estándar (DEBUG/INFO/WARNING/ERROR) y documentar cuándo usar cada uno.

### 8.2 Health checks

| Nivel | Endpoint/Mecanismo | Detalle |
|---|---|---|
| **HTTP** | `GET /health` | Endpoint Flask, verificado en CI (E2E) |
| **Docker** | `HEALTHCHECK` en Dockerfile | `curl -f http://localhost:${PORT}/health`, interval 30s, start-period 15s |
| **Compose** | `healthcheck:` en `db` y `app` | PostgreSQL: `pg_isready`, App: curl `/health` |

### 8.3 Métricas y trazas

- ❌ **No encontrado**: no hay Prometheus, OpenTelemetry, Datadog ni similar.
- `TODO:` Evaluar si se necesitan métricas (latencia de endpoints, tiempo de generación de escenarios).

### 8.4 Error tracking

- ❌ **No encontrado**: no hay Sentry, Rollbar ni similar.
- `TODO:` Evaluar integración de Sentry para errores en producción.

### 8.5 Manejo de errores

Patrón por capas:

```
domain/        → raise ValidationError / NotFoundError / ForbiddenError
application/   → propaga (no captura, no transforma)
infrastructure/→ propaga o envuelve en DomainError
adapters/      → mapea a HTTP: ValidationError→400, NotFoundError→404, ForbiddenError→403, Exception→500
```

Documentado en `context/architecture/error-model.md`.

---

## 9. Rendimiento y calidad no funcional

### 9.1 Puntos a vigilar

| Área | Riesgo | Mitigación actual |
|---|---|---|
| **Generación SVG** | CPU-bound para mapas complejos | `SvgMapRenderer` en infrastructure (single-threaded) |
| **Queries DB** | N+1 en listas de cards/favorites | `TODO:` Verificar con SQLAlchemy query logging |
| **Gradio startup** | Carga inicial lenta (~4s, 130+ componentes) | Composition root lazy-loaded |
| **Docker image size** | Multi-stage build | `python:3.11-slim`, sin dev tools en final |
| **Session store** | En memoria (default) o PostgreSQL | Configurable por entorno |

### 9.2 Cómo perfilar

- **Complejidad ciclomática**: `radon cc src -a -nc` (ya disponible).
- **Queries SQL**: `TODO:` Habilitar `echo=True` en SQLAlchemy session para profiling local.
- **Tiempo de tests**: `pytest --durations=20` para los 20 tests más lentos.
- **Build time**: medido implícitamente en CI (artifact timestamp).

---

## 10. Mantenibilidad y refactor

### 10.1 Reglas de refactor seguro

1. **Siempre con tests verdes** — nunca refactorizar con tests rotos.
2. **RED → GREEN → REFACTOR** — no mezclar nuevas features con refactor.
3. **Commits pequeños** — un cambio lógico por commit.
4. **Verificar imports** — `ruff check .` tras mover/renombrar módulos.
5. **Verificar contrato** — `STRICT_KWARGS_CONTRACT=1 pytest tests/unit/.../test_wire_events_contract.py` tras cambiar namespace o firma.
6. **Facades <450 LOC** — si un wire module supera 450, extraer a paquete interno `_nombre/`.

### 10.2 Checklist de code review

- [ ] ¿Los tests de la feature están presentes y pasan?
- [ ] ¿La cobertura de domain sigue en 100%?
- [ ] ¿La cobertura de application sigue ≥80%?
- [ ] ¿Ruff y Black están limpios?
- [ ] ¿Se respeta la política de imports (unidireccional, sin `src.`)?
- [ ] ¿`domain/` no importa de ninguna otra capa?
- [ ] ¿Los adapters no contienen lógica de negocio?
- [ ] ¿Los use cases usan DTOs y `.execute()`?
- [ ] ¿Las funciones nuevas tienen docstring?
- [ ] ¿Se usa `ValidationError` para errores de entrada (no `ValueError`)?
- [ ] ¿La autenticación/autorización es deny-by-default?
- [ ] ¿No se exponen datos de otros actores (anti-IDOR)?
- [ ] ¿Los módulos nuevos tienen <450 LOC? Si superan, ¿hay plan de split?
- [ ] ¿El CHANGELOG está actualizado?
- [ ] ¿Los nombres siguen las convenciones (snake_case, PascalCase, etc.)?
- [ ] ¿No hay magic numbers sin explicación?
- [ ] ¿No se loguean credenciales ni datos sensibles?
- [ ] ¿Se usa `defusedxml` si hay parsing de XML/SVG?
- [ ] ¿El PR template está completado?

### 10.3 Deuda técnica

- **Registro**: no hay sistema formal de tracking de deuda técnica.
- `TODO:` Crear label `tech-debt` en GitHub Issues para registrar deuda.
- `TODO:` Documentar decisiones de compromiso en ADRs si se crean.
- Deuda conocida actualmente:
  - `wire_events/__init__.py` tiene ~130 parámetros keyword-only (mitigado con golden contract test).
  - Adapters representan 65% del código (inherente al tamaño de la UI Gradio).
  - CHANGELOG con solo 3 entradas (proyecto en fase alpha).

---

## 11. Cómo ejecutar los checks de calidad en local

### 11.1 Instalación

```powershell
# Crear y activar entorno virtual
python -m venv venv311
.\venv311\Scripts\Activate.ps1     # Windows
# source venv311/bin/activate      # Linux/Mac

# Instalar dependencias de producción + test
pip install -r requirements.txt

# (Opcional) Instalar herramientas de análisis adicional
pip install -r requirements-dev.txt
```

### 11.2 Lint y formato

```bash
# Lint (bloquea CI si falla)
ruff check .

# Formato (bloquea CI si falla)
black --check src tests

# Auto-fix de imports y formato
ruff check --fix .
black src tests
```

### 11.3 Type-check

```bash
mypy src
```

### 11.4 Tests

```bash
# Tests unitarios (rápido, sin DB)
pytest tests/unit -q

# Tests de integración (requiere PostgreSQL)
RUN_DB_TESTS=1 pytest tests/integration -q       # Linux
$env:RUN_DB_TESTS="1"; pytest tests/integration -q   # PowerShell

# Todos (unit + integration)
pytest tests/unit tests/integration -q

# E2E (requiere docker-compose up)
pytest -m e2e -q

# Con cobertura
pytest tests/unit --cov=src --cov-report=term-missing

# Tests más lentos
pytest tests/unit --durations=20
```

### 11.5 Contrato kwargs (golden test)

```bash
# Normal (strict tests se saltan)
pytest tests/unit/adapters/ui_gradio/ui/test_wire_events_contract.py -v

# Simulando CI (strict mode)
$env:STRICT_KWARGS_CONTRACT="1"; pytest tests/unit/adapters/ui_gradio/ui/test_wire_events_contract.py -v   # PowerShell
STRICT_KWARGS_CONTRACT=1 pytest tests/unit/adapters/ui_gradio/ui/test_wire_events_contract.py -v           # bash
```

### 11.6 Análisis de seguridad y calidad (dev-only)

```bash
# SAST
bandit -r src

# Complejidad ciclomática
radon cc src -a

# Código muerto
vulture src --min-confidence 80

# Duplicación
pylint --disable=all --enable=duplicate-code src

# Todo junto (vía Makefile)
make quality
```

### 11.7 Docker local

```bash
# Levantar stack completo (PostgreSQL + App)
docker compose up -d --build

# Verificar salud
curl http://localhost:8000/health

# Bajar
docker compose down
```

---

## 12. Anexos — inventario de herramientas detectadas

### 12.1 Archivos de configuración

| Archivo | Propósito |
|---|---|
| `pyproject.toml` | Ruff, Pylint, Radon, Vulture, mypy, Bandit — configuración central |
| `pytest.ini` | pytest: pythonpath, markers (`e2e`, `db`), warning filters |
| `requirements.txt` | Dependencias de producción + test (pinned) |
| `requirements-dev.txt` | Herramientas de análisis adicionales (dev-only) |
| `Dockerfile` | Multi-stage build: base → deps → final (non-root) |
| `docker-compose.yml` | Stack: PostgreSQL 16 + Combined App (FastAPI+Flask+Gradio) |
| `alembic.ini` | Alembic: migraciones DB |
| `Makefile` | Targets: install, lint, test, quality, docker |
| `.github/workflows/ci.yml` | CI principal: lint, unit, integration, docker, manual |
| `.github/workflows/e2e.yml` | E2E manual: Playwright + docker-compose |
| `.github/pull_request_template.md` | Template de PR con checklists de calidad |
| `.github/instructions/snyk_rules.instructions.md` | Regla Copilot para escaneo Snyk |

### 12.2 Archivos de documentación de contexto

| Archivo | Propósito |
|---|---|
| `AGENTS.md` | Índice de contexto + reglas globales mínimas |
| `context/quality/tdd.md` | Ciclo RED → GREEN → REFACTOR |
| `context/quality/testing-strategy-60-30-10.md` | Pirámide 60/30/10 |
| `context/quality/coverage-policy-100-80-0.md` | Política de cobertura por capa |
| `context/quality/definition-of-done.md` | Definition of Done completa |
| `context/quality/solid-checklist.md` | Checklist SOLID práctico |
| `context/architecture/layers.md` | Arquitectura de 4 capas |
| `context/architecture/import-policy.md` | Política de imports unidireccional |
| `context/architecture/error-model.md` | Jerarquía de errores y mapeo HTTP |
| `context/architecture/facade-pattern.md` | Patrón facade + módulos internos |
| `context/security/security-by-design.md` | Principios de seguridad |
| `context/security/authz-anti-idor.md` | Anti-IDOR y autorización |
| `context/security/input-validation.md` | Validación de entrada |
| `context/security/secrets-and-config.md` | Gestión de secretos |
| `context/security/auth-demo.md` | Sistema de autenticación demo |

### 12.3 Versiones de herramientas

| Herramienta | Versión | Origen |
|---|---|---|
| Python | 3.11 | `pyproject.toml`, CI `PYTHON_VERSION` |
| Flask | 3.0.2 | `requirements.txt` |
| Gradio | 4.44.1 | `requirements.txt` |
| SQLAlchemy | 2.0.32 | `requirements.txt` |
| Alembic | 1.13.2 | `requirements.txt` |
| PostgreSQL | 16-alpine | `docker-compose.yml` |
| pytest | 8.2.0 | `requirements.txt` |
| pytest-cov | 5.0.0 | `requirements.txt` |
| ruff | 0.5.6 | `requirements.txt`, CI `RUFF_VERSION` |
| black | 24.8.0 | `requirements.txt` |
| mypy | 1.8.0 | `requirements-dev.txt` |
| bandit | 1.7.6 | `requirements-dev.txt` |
| pylint | 3.0.3 | `requirements-dev.txt` |
| radon | 6.0.1 | `requirements-dev.txt` |
| vulture | 2.10 | `requirements-dev.txt` |
| Playwright | 1.49.0 | `requirements.txt` |
| pydantic | 2.8.2 | `requirements.txt` |
| defusedxml | 0.7.1 | `requirements.txt` |
| gunicorn | 22.0.0 | `requirements.txt` |
| waitress | 3.0.0 | `requirements.txt` |
