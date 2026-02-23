# Patrón Facade — Wiring Gradio

## Problema

Los módulos de wiring de Gradio tienden a convertirse en **god-modules** (500+
líneas) que mezclan:
- Binding de eventos (`.click()`, `.change()`)
- Lógica de transformación
- Construcción de payloads
- Actualización de UI

Esto viola SRP, dificulta el testing y bloquea la review.

## Solución

Cada feature tiene un **facade público** (`wire_*.py`, 250–450 líneas) que
**solo** contiene wiring de Gradio, delegando toda la lógica a **módulos
internos** prefijados con `_`.

```
wiring/
├── wire_scenography.py          ← Facade (público)
└── _scenography/                ← Internal package
    ├── __init__.py
    ├── _form_state.py           ← Estado de formulario (puro Python)
    ├── _polygon.py              ← Geometría de polígonos (puro Python)
    ├── _ui_updates.py           ← gr.update() builders
    └── _builder.py              ← Constructores de shapes
```

## Reglas

### Facades (`wire_*.py`)

| Regla | Límite |
|-------|--------|
| Longitud máxima | 450 líneas (ideal < 350) |
| Contenido | Solo `.click()`, `.change()`, `.submit()` + imports |
| Lógica de negocio | **Cero** — delegar siempre |
| Tests directos | No necesarios (testear internals) |

### Módulos internos (`_*.py`)

| Regla | Detalle |
|-------|---------|
| Prefijo | `_` obligatorio (indica "privado") |
| Gradio imports | Solo en `_ui_updates.py` (los demás son pure Python) |
| Testabilidad | 1 archivo de test por módulo interno |
| Cobertura | ≥ 80 % |

## Packages completados

| Package | Módulos | Tests | Facade |
|---------|---------|-------|--------|
| `_detail/` | `_render.py`, `_converters.py` | 45 tests | `wire_detail.py` |
| `_deployment/` | `_form_state.py`, `_geometry.py`, `_ui_updates.py`, `_zone_builder.py` | 83 tests | `wire_deployment_zones.py` |
| `_scenography/` | `_form_state.py`, `_polygon.py`, `_ui_updates.py`, `_builder.py` | 71 tests | `wire_scenography.py` |
| `_generate/` | `_preview.py`, `_create_logic.py`, `_resets.py`, `_outputs.py` | 44 tests | `wire_generate.py` |

**Total**: 14 módulos internos, 243 tests de wiring.

## Workflow de extracción

```
1. BASELINE  → pytest -q (todos los tests verdes)
2. AUDIT     → Identificar lógica extraíble en el facade
3. EXTRACT   → Mover a módulo interno con prefijo _
4. TEST      → Escribir tests para el módulo extraído
5. FACADE    → Actualizar facade para importar del módulo
6. VERIFY    → pytest -q + ruff check (todo verde)
```

## Cuándo NO aplicar

- Facades simples (< 250 líneas) que no tienen lógica extraíble.
- Facades que solo hacen binding directo sin transformación.
- No crear packages vacíos "por si acaso".

## Ejemplo: wire_scenography.py

```python
# FACADE — solo wiring
from adapters.ui_gradio.ui.wiring._scenography._form_state import (
    add_scenography_item,
    remove_last_item,
)
from adapters.ui_gradio.ui.wiring._scenography._builder import (
    build_scenography_shapes,
)

def wire_scenography(app, components, api_client):
    components.btn_add.click(
        fn=add_scenography_item,
        inputs=[components.state],
        outputs=[components.state, components.list_display],
    )
    components.btn_remove.click(
        fn=remove_last_item,
        inputs=[components.state],
        outputs=[components.state, components.list_display],
    )
```
