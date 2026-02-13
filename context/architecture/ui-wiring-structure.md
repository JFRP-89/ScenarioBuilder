# Estructura de UI Wiring (Gradio)

## Ubicación
`src/adapters/ui_gradio/ui/wiring/`

## Propósito
Capa de wiring que conecta componentes Gradio con servicios de aplicación.

**No contiene lógica de negocio** — solo orquestación de eventos UI.

## Estructura Actual

```
wiring/
├── __init__.py              # wire_events() dispatcher
│
├── wire_detail.py           # Detail page (view/edit/delete)
├── wire_deployment_zones.py # Deployment zones form
├── wire_fav_toggle.py       # Favorite toggle button
├── wire_favorites.py        # Favorites list
├── wire_generate.py         # Generate preview + create scenario
├── wire_home.py             # Home page (recent cards)
├── wire_list.py             # List cards page
├── wire_navigation.py       # Page navigation
├── wire_objectives.py       # Objectives form
├── wire_scenography.py      # Scenography form
├── wire_special_rules.py    # Special rules dropdown
├── wire_table.py            # Table size form
├── wire_victory_points.py   # Victory points dropdown
├── wire_view.py             # View-only page
├── wire_visibility.py       # Visibility & sharing
│
├── _detail/                 # Internal: detail page helpers
│   ├── __init__.py
│   ├── _render.py           # HTML rendering
│   └── _converters.py       # API → UI state
│
├── _deployment/             # Internal: deployment zones helpers
│   ├── __init__.py
│   ├── _form_state.py       # Form defaults & selected state
│   ├── _geometry.py         # Pure geometric calculations
│   ├── _ui_updates.py       # gr.update() builders
│   └── _zone_builder.py     # Zone builder (never-raise)
│
├── _scenography/            # Internal: scenography helpers
│   ├── __init__.py
│   ├── _form_state.py       # Form defaults & selected state
│   ├── _polygon.py          # Polygon parsing & conversion
│   ├── _ui_updates.py       # Type visibility helpers
│   └── _builder.py          # Scenography builder (never-raise)
│
└── _generate/               # Internal: generate helpers
    ├── __init__.py
    ├── _preview.py          # Preview & render delegation
    ├── _create_logic.py     # Pure validation logic
    ├── _resets.py           # Form reset builders
    └── _outputs.py          # Stay-on-page tuple builder
```

## Convenciones de Nombres

### Facades Públicos (wire_*.py)
- **Patrón**: `wire_<feature>.py`
- **Función principal**: `wire_<feature>(**components)`
- **Responsabilidad**: Vincular eventos Gradio (`.click()`, `.change()`)
- **Tamaño**: 250-450 líneas (objetivo <350)

### Paquetes Internos (_*/-)
- **Patrón**: `_<feature>/`
- **Propósito**: Helpers testables, no API pública
- **Marcado**: `__init__.py` con "Internal helpers — not a public API"

### Módulos Internos (_*.py)
| Nombre | Propósito | Gradio? |
|--------|-----------|---------|
| `_logic.py` / `_create_logic.py` | Validaciones puras, reglas | ❌ No |
| `_form_state.py` | Defaults, estado de formularios | ❌ No |
| `_converters.py` | API ↔ UI mappers | ❌ No |
| `_render.py` | HTML rendering | ❌ No |
| `_geometry.py` | Cálculos geométricos puros | ❌ No |
| `_polygon.py` | Parsers de coordenadas | ❌ No |
| `_ui_updates.py` | Builders de `gr.update()` | ✅ Sí |
| `_resets.py` | Form reset helpers | ✅ Sí |
| `_outputs.py` | Tuple builders para outputs | ✅ Sí |
| `_builder.py` | Domain builders complejos | ❌ No |
| `_preview.py` | Delegation helpers | Mixto |
| `_zone_builder.py` | Builders específicos de dominio | ❌ No |

## Flujo de Datos

```
Usuario interactúa con UI (Gradio)
    ↓
wire_<feature>() captura evento (.click / .change)
    ↓
Delega a helper interno (_feature/_*.py)
    ↓
[Si es lógica pura] → Retorna dato validado
[Si es API call] → Llama a services.generate / handle_*
[Si es UI update] → Retorna gr.update(...)
    ↓
Gradio actualiza componentes
```

## Patrones Comunes

### 1. Preview + Render (wire_generate)
```python
# Facade delega a _preview.py
generate_btn.click(
    fn=preview_and_render,  # De _generate/_preview.py
    inputs=[...],
    outputs=[output, svg_preview]
)
```

### 2. Validación Pura (wire_generate)
```python
# Inner function delega a _create_logic.py
def _on_create_scenario(preview_data, edit_id=""):
    ok, err_msg = validate_preview_data(preview_data)  # Pure
    if not ok:
        return _stay(err_msg)
```

### 3. Form State (wire_scenography, wire_deployment_zones)
```python
# Facade delega a _form_state.py
from _scenography._form_state import default_scenography_form

def _on_add_scenography():
    return default_scenography_form()  # No Gradio, pure data
```

### 4. UI Updates (wire_deployment_zones)
```python
# Facade delega a _ui_updates.py
from _deployment._ui_updates import triangle_visibility_updates

def _on_deployment_type_change(dtype):
    return triangle_visibility_updates(dtype == "triangle")
```

### 5. Builders Never-Raise (wire_scenography, wire_deployment_zones)
```python
# Facade delega a _builder.py
from _scenography._builder import build_scenography_data

def _on_add_scenography(sceno_type, ...):
    data, error_msg = build_scenography_data(sceno_type, ...)
    if error_msg:
        return _error_state(error_msg)
    return _success_state(data)
```

## Testing

### Estructura de Tests
```
tests/unit/adapters/ui_gradio/ui/wiring/
├── test_<facade>_<internal>.py   # 1 test por módulo interno
│
├── test_generate_create_logic.py # _generate/_create_logic.py
├── test_generate_resets.py       # _generate/_resets.py
├── test_generate_outputs.py      # _generate/_outputs.py
│
├── test_scenography_form_state.py
├── test_scenography_polygon.py
├── test_scenography_builder.py
├── test_scenography_ui_updates.py
│
├── test_deployment_form_state.py
├── test_deployment_geometry.py
├── test_deployment_ui_updates.py
└── test_deployment_zone_builder.py
```

### Estrategia de Tests
- **Módulos puros (sin Gradio)**: 80%+ cobertura, fácil de testear
- **Módulos con Gradio**: Tests de forma/outputs, no de componentes reales
- **Facades**: Minimal testing (integration tests cubren wiring)

## Dependencias Permitidas

### Facades (wire_*.py)
```python
import gradio as gr  # ✅ Necesario para wiring
from adapters.ui_gradio.services.generate import handle_preview  # ✅ Services
from adapters.ui_gradio.ui.router import navigate_to  # ✅ Routing
from adapters.ui_gradio.ui.wiring._generate._preview import preview_and_render  # ✅ Internals
```

### Módulos Internos Puros (_logic.py, _geometry.py, etc.)
```python
from typing import Any  # ✅
import math  # ✅
from domain.models import DeploymentZone  # ✅ Domain models OK

import gradio as gr  # ❌ NO en módulos puros
from adapters.ui_gradio.services import ...  # ❌ Services solo en facades
```

### Módulos Internos con Gradio (_ui_updates.py, _resets.py)
```python
import gradio as gr  # ✅ Permitido para gr.update()
from adapters.ui_gradio.ui.components.svg_preview import _PLACEHOLDER_HTML  # ✅ Constants OK

from adapters.ui_gradio.services import ...  # ❌ No services, solo facades llaman services
```

## Métricas de Calidad

| Facade | Líneas | Internals | Tests | Status |
|--------|--------|-----------|-------|--------|
| wire_generate | 280 | 4 | 44 | ✅ |
| wire_scenography | 426 | 4 | 71 | ✅ |
| wire_deployment_zones | 426 | 4 | 83 | ✅ |
| wire_detail | ~350 | 2 | 45 | ✅ |
| wire_table | ~250 | 0 | 0 | 🟡 Simple |
| wire_objectives | ~200 | 0 | 0 | 🟡 Simple |
| wire_victory_points | ~150 | 0 | 0 | 🟡 Simple |
| wire_special_rules | ~150 | 0 | 0 | 🟡 Simple |
| wire_visibility | ~200 | 0 | 0 | 🟡 Simple |
| wire_home | ~150 | 0 | 0 | 🟡 Simple |
| wire_navigation | ~100 | 0 | 0 | 🟡 Simple |
| wire_list | ~200 | 0 | 0 | 🟡 Simple |
| wire_view | ~200 | 0 | 0 | 🟡 Simple |
| wire_favorites | ~150 | 0 | 0 | 🟡 Simple |
| wire_fav_toggle | ~100 | 0 | 0 | 🟡 Simple |

**Total**: 15 facades, 4 paquetes internos (14 módulos), 243 tests wiring

## Evolución

### Completado (Feb 2026)
- ✅ wire_detail → _detail/ (2 módulos, 45 tests)
- ✅ wire_deployment_zones → _deployment/ (4 módulos, 83 tests)
- ✅ wire_scenography → _scenography/ (4 módulos, 71 tests)
- ✅ wire_generate → _generate/ (4 módulos, 44 tests)

### Candidatos Futuros
- 🔄 wire_table: Simple, probablemente no necesita split
- 🔄 wire_objectives: Simple, OK como está
- 🔄 wire_victory_points: Simple, OK como está
- 🔄 Otros facades <250 líneas: No requieren refactor

## Referencias Cruzadas
- Ver `context/architecture/facade-pattern.md` para el patrón general y anti-patrones
- Ver `context/quality/testing-strategy-60-30-10.md` para estrategia de testing
- Ver `context/architecture/layers.md` para separación de capas
