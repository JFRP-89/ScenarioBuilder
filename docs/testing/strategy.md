# Estrategia de Testing — Scenario Builder

## Visión general

Estrategia **60/30/10** (unit/integration/e2e) con cobertura verificada en
capas internas y characterization tests como safety net para refactoring.

---

## Distribución de tests

```
 ┌───────────────────────────┐
 │  Unit Tests (60%)         │  1972 tests
 │  Domain: 100% coverage    │  Fast (<1ms), sin IO
 │  Application: 99% coverage│  Wiring internals: ≥80%
 ├───────────────────────────┤
 │  Integration Tests (30%)  │  1000+ tests
 │  Repos, bootstrap, Flask  │  Con BD o mocks
 │  routes, Gradio smoke     │  Database tests included
 ├───────────────────────────┤
 │  E2E Tests (10%)          │  100+ tests
 │  CRUD flows, authz,       │  Flask + in-memory repos
 │  security scenarios       │
 └───────────────────────────┘
```

**Total actual**: 3064+ tests pasando, 0 failures, 100% success rate con BD habilitada.

---

## Cobertura por capa

| Capa | Objetivo | Estado | Verificado |
|------|----------|--------|------------|
| `domain/` | 100% | ✅ **100%** (732 statements) | Sí |
| `application/` | ≥ 80% | ✅ **99%** (810 statements) | Sí |
| `infrastructure/` | Sin gate | — | — |
| `adapters/` | Sin gate | — | — |

### Política

- **Domain 100%**: Cada branch, cada edge case, cada error path. Obligatorio en PR.
- **Application ≥80%**: Todos los use cases, DTOs, validaciones. Exceeds objective (99%).
- **Infra/adapters**: Cobertura pragmática. No se bloquea merge por coverage bajo,
  pero se testea lo crítico (repos, auth, SVG sanitization).

Verificación: `pytest --cov=src/domain --cov-fail-under=100 tests/unit` para domain verificación.
Verificado último: 3064+ tests con `RUN_DB_TESTS=1` y `DATABASE_URL_TEST` configurada.

---

## Tipos de tests

### Unit Tests

Tests de funciones y clases aisladas, sin IO ni dependencias externas.

**Ubicación**: `tests/unit/`

**Qué testean**:

| Área | Ejemplos |
|------|----------|
| Domain models | `Card.__post_init__`, `TableSize.from_cm()`, `MapSpec` validations |
| Domain logic | `generate_card()`, `matched_score()`, `incompatible_pairs_ok()` |
| Seed handling | `normalize_seed()`, `get_rng()`, `derive_attempt_seed()` |
| AuthZ | `can_read()`, `can_write()`, `parse_visibility()` |
| Validation | `validate_non_empty_str()`, `validate_seed()` |
| Use cases | `execute()` con repos mockeados |
| Wiring internals | `_form_state`, `_geometry`, `_polygon`, `_preview` |
| Gradio helpers | Conversiones, parsing, payload builders, special rules |

**Características**:
- Sin acceso a BD, red ni filesystem.
- Ejecución < 1ms por test.
- Parametrizados con `@pytest.mark.parametrize`.
- Fixtures mínimas, datos inline.

### Integration Tests

Tests que verifican la interacción entre componentes.

**Ubicación**: `tests/integration/`

**Qué testean**:

| Área | Ejemplos |
|------|----------|
| Repositories | CRUD completo contra in-memory repos |
| Bootstrap | `build_services()` con mocks/stubs |
| Flask routes | Request/response con `test_client()` |
| Gradio smoke | `build_app()` no hace HTTP, retorna `gr.Blocks` |
| SVG renderer | Renderizado completo con shapes reales |
| Generation pipeline | Seed → shapes → card → SVG (end-to-end interno) |
| Session store | Creación, lookup, invalidación de sesiones |

**Características**:
- Pueden usar repositorios in-memory.
- Tests de BD requieren `DATABASE_URL_TEST` y `RUN_DB_TESTS=1` (skip si no disponible).
- 100+ tests marcados con `@pytest.mark.db` para ejecución condicional.
- Usan `test_client()` de Flask, no HTTP real.

### E2E Tests

Tests que ejercitan el flujo completo del usuario.

**Ubicación**: `tests/e2e/`

**Qué testean**:

| Flujo | Escenarios |
|-------|-----------|
| CRUD de cards | Create → Read → Update → Delete |
| Favoritos | Toggle → List → Cleanup on delete |
| Visibilidad | Private access denied, Shared access granted, Public visible |
| AuthZ anti-IDOR | Acceso a card de otro usuario → 403 |
| Autenticación | Register → Login → Profile → Logout |
| Error handling | Input inválido → 400, Card inexistente → 404 |

---

## Fixtures principales

```python
# tests/conftest.py

@pytest.fixture
def services():
    """Build fresh services with in-memory repos."""
    return build_services()

@pytest.fixture
def card_repo():
    """In-memory card repository."""
    return InMemoryCardRepository()

@pytest.fixture
def favorites_repo():
    """In-memory favorites repository."""
    return InMemoryFavoritesRepository()
```

---

## Characterization Tests (Gradio)

Tests escritos para **congelar el comportamiento actual** del Gradio adapter
sin modificar código. Actúan como safety net para refactoring.

### Inventario

| Test file | Tests | Qué congela |
|-----------|-------|------------|
| `test_unit_conversions.py` | 24 | `_convert_to_cm()`, `_convert_from_cm()`, `_build_custom_table_payload()` |
| `test_parsing_helpers.py` | 24 | `_parse_json_list()`, `_parse_deployment_shapes()`, `_parse_map_specs()` |
| `test_special_rules_helpers.py` | 25 | `_validate_special_rules()`, `_add_special_rule()`, `_remove_last_special_rule()` |
| `test_payload_ui_helpers.py` | 27 | `_build_generate_payload()`, `_apply_table_config()`, preset+unit changes |
| `test_validation.py` | 10 | `_validate_required_fields()` |
| `test_gradio_app_smoke.py` | 11 | Import safety, `build_app()`, API base URL, headers |

**Total**: 121 characterization tests.

### Hallazgos documentados

1. `seed=0` es falsy en Python → se trata como None (modo manual).
2. `gr.update()` retorna dict, no objeto con atributos.
3. `API_BASE_URL` siempre se normaliza quitando trailing slash.
4. Custom table limits: 60–300 cm con validación en payload builder.
5. Special rules helpers no mutan estado original (inmutabilidad).

---

## Wiring Tests (Facade Internals)

Tests para los módulos internos extraídos del patrón facade.

| Package | Tests | Módulos internos |
|---------|-------|-----------------|
| `_detail/` | 45 | `_render.py`, `_converters.py` |
| `_deployment/` | 83 | `_form_state.py`, `_geometry.py`, `_ui_updates.py`, `_zone_builder.py` |
| `_scenography/` | 71 | `_form_state.py`, `_polygon.py`, `_ui_updates.py`, `_builder.py` |
| `_generate/` | 44 | `_preview.py`, `_create_logic.py`, `_resets.py`, `_outputs.py` |

**Total**: 243 wiring tests. Cobertura ≥ 80% por módulo interno.

---

## Comandos

### Ejecutar todos los tests

```bash
pytest -q
```

### Por categoría

```bash
pytest tests/unit -q                    # Solo unit
pytest tests/integration -q             # Solo integration
pytest tests/e2e -q                     # Solo e2e
```

### Por capa

```bash
pytest tests/unit/domain/ -v            # Domain
pytest tests/unit/application/ -v       # Application
pytest tests/unit/adapters/ -v          # Adapters
pytest tests/unit/infrastructure/ -v    # Infrastructure
```

### Con cobertura

```bash
pytest --cov=src --cov-report=html      # Reporte HTML en htmlcov/
pytest --cov=src/domain --cov-fail-under=100   # Gate domain 100%
pytest --cov=src/application --cov-fail-under=80  # Gate application 80%
```

### Utilidades

```bash
pytest -x                   # Detener en primer fallo
pytest -k "create"          # Tests que matchean patrón
pytest --lf                 # Re-ejecutar solo tests fallidos
pytest -v --tb=short        # Verbose con tracebacks cortos
pytest --durations=10       # 10 tests más lentos
```

---

## Convenciones de testing

### Naming

```python
# test_<module>.py
def test_<action>_<scenario>_<expected>():
    """Dado <contexto>, cuando <acción>, entonces <resultado>."""
```

### Estructura AAA

```python
def test_create_card_with_valid_seed_returns_card():
    # Arrange
    seed = 42
    table = TableSize.standard()
    
    # Act
    card = generate_card(mode="casual", seed=seed, ...)
    
    # Assert
    assert card.seed == 42
    assert card.mode == GameMode.CASUAL
```

### Parametrización

```python
@pytest.mark.parametrize("seed,expected", [
    (0, 0),
    (42, 42),
    ("123", 123),
    (3.0, 3),
])
def test_normalize_seed_valid_values(seed, expected):
    assert normalize_seed(seed) == expected
```

---

## TDD Workflow

```
RED    → Escribir test que falla
GREEN  → Implementar código mínimo para que pase
REFACTOR → Mejorar sin romper tests

Si el prompt dice "solo tests" → NO tocar src/
```

---

## CI Integration

```yaml
# Propuesta de CI (GitHub Actions)
steps:
  - run: ruff check .              # Lint
  - run: pytest -q                  # All tests
  - run: pytest --cov=src/domain --cov-fail-under=100  # Coverage gates
  - run: pytest --cov=src/application --cov-fail-under=80
```

Nada se mergea con CI en rojo.
