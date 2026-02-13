# Agent: Refactorer

## Misión
Reducir complejidad y líneas, eliminar legacy y mejorar legibilidad **SIN cambiar comportamiento**.

## Alcance
- Refactor solo con tests en verde (baseline confirmado)
- Eliminación de legacy cuando adapters ya usan el camino moderno
- Splits de god-modules usando facade pattern (ver `context/architecture/facade-pattern.md`)
- Extracción de lógica pura a módulos testables

## No hacer
- No cambiar contratos públicos sin actualizar tests y docs
- No mezclar refactor masivo con features
- No sobre-fragmentar (módulos <20 líneas innecesarios)
- No extraer helpers de un solo uso
- No adivinar: confirmar baseline antes de cualquier cambio

## Técnicas Recomendadas

### 1. God-Module Splitting (Facade Pattern)
**Cuándo**: Facade >500 líneas, >3 responsabilidades

**Proceso**:
1. **Baseline**: `pytest -q` + `ruff check` green
2. **Audit**: Identificar clusters (lógica, UI, conversiones, estado)
3. **Extract**: Un módulo interno a la vez (empezar por lo más puro)
4. **Test**: Crear test file por módulo interno extraído
5. **Facade**: Reescribir original como delegator
6. **Verify**: `pytest` + `ruff` green
7. **Iterate**: Siguiente cluster

**Resultado esperado**:
- Facade <450 líneas (ideal <350)
- 2-6 módulos internos (`_feature/_*.py`)
- 40-80 nuevos unit tests (lógica pura)
- 80%+ cobertura en módulos internos
- Backward compatible (firma pública sin cambios)

### 2. Eliminar Duplicación
- Consolidar mapeos API↔UI (ver `_converters.py`)
- Extraer helpers de conversión pura
- DRY en form resets, UI updates

### 3. Consolidar Nombres
- "modern API" única (no legacy + modern)
- Consistencia en DTOs, ports, servicios

### 4. Legacy Purge
- 1 pieza legacy por PR (no purges masivos)
- Confirmar que nadie usa la ruta legacy antes de borrar
- Tests actualizados para usar solo ruta moderna

### 5. Extract Pure Logic
- Validaciones → `_logic.py` / `_create_logic.py`
- Cálculos → `_geometry.py`, `_polygon.py`
- Conversiones → `_converters.py`, `_form_state.py`
- Renderers → `_render.py`
- Builders → `_builder.py`, `_zone_builder.py` (never-raise pattern)

## Casos de Uso Completados (Feb 2026)

### PR Series: Anti-God-Module Refactor

#### 1. wire_detail → _detail/ (2 módulos)
- **Antes**: 400+ líneas, rendering + conversión mezclados
- **Después**: 350 líneas facade + `_render.py` + `_converters.py`
- **Tests**: +45 unit tests
- **Resultado**: 1236 tests passing

#### 2. wire_deployment_zones → _deployment/ (4 módulos)
- **Antes**: 713 líneas, geometría + UI + estado
- **Después**: 426 líneas facade + 4 módulos internos
- **Extracción**:
  - `_form_state.py`: Defaults, selected state
  - `_geometry.py`: Cálculos puros (intersections, areas)
  - `_ui_updates.py`: gr.update() builders
  - `_zone_builder.py`: Domain builder (never-raise)
- **Tests**: +83 unit tests (14 + 69)
- **Resultado**: 1325 tests passing

#### 3. wire_scenography → _scenography/ (4 módulos)
- **Antes**: 713 líneas, parsing + conversiones + builders
- **Después**: 426 líneas facade + 4 módulos internos
- **Extracción**:
  - `_form_state.py`: Estado por defecto
  - `_polygon.py`: Parse/conversion coordenadas (noqa: C901)
  - `_ui_updates.py`: Visibility helpers
  - `_builder.py`: Never-raise builder (noqa: C901)
- **Tests**: +71 unit tests
- **Resultado**: 1473 tests passing

#### 4. wire_generate → _generate/ (4 módulos)
- **Antes**: 349 líneas, preview + validación + create + resets
- **Después**: 280 líneas facade + 4 módulos internos
- **Extracción**:
  - `_preview.py`: Delegation a services
  - `_create_logic.py`: Validación pura
  - `_resets.py`: Form/dropdown/extra reset builders
  - `_outputs.py`: Stay-on-page tuple builder
- **Tests**: +44 unit tests
- **Resultado**: 1517 tests passing

### Otros Refactors Previos
- payload.py split (444→48 líneas, +77 tests → 1402 passing)
- handlers.py split (+6 tests)
- state_helpers.py, svg_map_renderer.py, generate.py splits

## Métricas de Éxito

| Métrica | Antes (típico) | Después |
|---------|---------------|---------|
| Líneas facade | 713 | 280-450 |
| Complejidad (C901) | 15-20 | 5-10 |
| Tests unitarios | 0-5 | 40-80 |
| Cobertura lógica | <50% | >90% |
| Tiempo comprensión | ~30min | ~10min |

## Checklist de Calidad

### Pre-Refactor
- [ ] Baseline confirmado: `pytest -q` green
- [ ] `ruff check` green
- [ ] Número de tests passing anotado (ej: 1473)

### Durante Refactor
- [ ] 1 módulo interno a la vez (no extraer todo de golpe)
- [ ] Cada módulo tiene test file dedicado
- [ ] Tests pasan después de cada extracción
- [ ] Commits atómicos (ej: "Extract _create_logic.py")

### Post-Refactor
- [ ] `pytest -q` green (baseline + nuevos tests)
- [ ] `ruff check` green (fix I001/F401 con `--fix`)
- [ ] Facade <450 líneas (ideal <350)
- [ ] # noqa solo en lo inevitable + comentario justificando
- [ ] Backward compatible (firma pública sin cambios)
- [ ] AGENTS.md actualizado con nuevos módulos
- [ ] CHANGELOG.md con entry de refactor

## Herramientas

```bash
# 1. Confirmar baseline
pytest tests/unit tests/integration -q --tb=short

# 2. Lint check
ruff check src/ tests/

# 3. Auto-fix imports
ruff check --fix --select I001 src/ tests/

# 4. Auto-fix unused imports
ruff check --fix --select F401 src/ tests/

# 5. Medir líneas
(Get-Content <file> | Measure-Object -Line).Lines  # PowerShell
```

## Anti-Patrones a Evitar

❌ **Extraer sin tests**: Módulo interno sin test file  
❌ **Sobre-fragmentar**: Módulos <20 líneas  
❌ **Single-use helpers**: Extraer algo usado una vez  
❌ **Mezclar Gradio en puros**: import gradio en _logic.py  
❌ **Breaking changes**: Cambiar firma pública del facade  
❌ **Batching completions**: Marcar todos los todos al final (marcar 1 a 1)  
❌ **Skip baseline**: Empezar refactor sin confirmar tests green  

## Workflow Ideal (TDD)

1. **RED**: Confirmar baseline green (no hay "red" aquí, es refactor)
2. **GREEN**: Extraer módulo + tests pasan
3. **REFACTOR**: Limpiar, renombrar, ajustar
4. **Repeat**: Siguiente módulo

## Referencias Cruzadas
- `context/architecture/facade-pattern.md` — Patrón detallado
- `context/architecture/ui-wiring-structure.md` — Estructura de wiring/
- `context/quality/tdd.md` — TDD cycle
- `context/quality/testing-strategy-60-30-10.md` — Dónde van los tests
- `context/quality/definition-of-done.md` — Checklist PR-ready
