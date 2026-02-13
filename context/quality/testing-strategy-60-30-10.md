# Testing Strategy 60/30/10

## Distribución de Tests

### 60% Unit Tests
- **domain/**: Validaciones, invariantes, modelos
  - 100% cobertura objetivo
  - Tests rápidos (<1ms cada uno)
  - Sin IO, sin mocks complejos

- **application/**: Use cases con fakes/in-memory
  - DTOs + `.execute()` testing
  - Repos in-memory como fixtures
  - 80%+ cobertura

- **adapters/ui_gradio/ui/wiring/_**/**: Módulos internos puros
  - Lógica extraída de facades (validaciones, conversiones, cálculos)
  - Sin Gradio en tests (data structures puras)
  - 80%+ cobertura por módulo
  - Ejemplo: `test_generate_create_logic.py`, `test_scenography_polygon.py`

### 30% Integration Tests
- **infrastructure/**: Repos, generators, bootstrap
  - `build_services()` smoke tests
  - Wiring completo funciona
  - Flujo mínimo end-to-end dentro de la capa

- **adapters/http_flask/**: Rutas con cliente de prueba
  - Marshmallow schemas
  - Error mapping (ValidationError → 400)
  - Auth/authz (deny-by-default)

- **adapters/ui_gradio/**: Smoke tests de app
  - `build_app()` retorna Blocks
  - No tests de interacción UI complejos

### 10% E2E Tests
- **API completa**: Flask + repos in-memory
  - Client fixtures
  - Flujos críticos: create → read → update → delete
  - Casos de seguridad: IDOR, authz

- **Gradio (opcional)**: Solo smoke
  - No interacción UI real (UI testing manual)

## Estado Actual (Feb 2026)

| Capa | Tests | Cobertura |
|------|-------|----------|
| domain/ | ~200 | 100% |
| application/ | ~400 | 80% |
| infrastructure/ | ~300 | 80% |
| adapters/http_flask/ | ~150 | 70% |
| adapters/ui_gradio/ | ~450 | 60% |
| **TOTAL** | **1517** | **80%** |

### Distribución Real
- Unit: ~900 (59%)
- Integration: ~450 (30%)
- E2E: ~167 (11%)

🎯 **Objetivo cumplido**

## Reglas de Testing

### 1. No E2E antes de estable application+infra
- Primero: domain → application → infrastructure
- Luego: adapters (HTTP, UI)
- Finalmente: E2E flows

### 2. Módulos internos (_*/) = Unit tests priority
- Cada módulo interno → 1 test file
- Ejemplo: `_generate/_create_logic.py` → `test_generate_create_logic.py`
- Target: 80%+ cobertura por módulo

### 3. Facades = Minimal unit testing
- Los facades (wire_*.py) son wiring, no lógica
- Integration/E2E tests cubren wiring
- Unit tests solo para helpers inline complejos (si existen)

### 4. Fixtures ligeros
- Preferir data structures sobre mocks
- In-memory repos para application tests
- Client fixtures para integration tests

## Ejemplo: wire_generate Split

### Antes del Split
- 1 facade monolítico (349 líneas)
- 0 unit tests (lógica inline no testeable)
- Solo integration tests del flujo completo

### Después del Split
- 1 facade delegator (280 líneas)
- 4 módulos internos testables
- **44 nuevos unit tests** (100% cobertura lógica pura)
- Integration tests sin cambios (backward compatible)

#### Tests Creados
```
test_generate_create_logic.py  — 14 tests (validación pura)
test_generate_resets.py         — 17 tests (form/dropdown/extra resets)
test_generate_outputs.py        — 13 tests (tuple builders)
```

## Herramientas

- **pytest**: Test runner
- **pytest-cov**: Cobertura
- **coverage.json**: Report para tracking
- **ruff**: Linting pre-commit

## Referencias Cruzadas
- `context/quality/coverage-policy-100-80-0.md` — Targets de cobertura
- `context/quality/definition-of-done.md` — Checkli st para PRs
- `context/architecture/facade-pattern.md` — Por qué los internos son testables
