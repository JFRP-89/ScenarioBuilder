# SonarQube Wiring — Problemas Arquitecturales y Soluciones

**Fecha**: 2026-02-20  
**Scope**: `src/adapters/ui_gradio/ui/wiring/`  
**Estado**: 2921 tests passing, ruff clean, baseline establecido

---

## Resumen ejecutivo

Tras completar la campaña de SonarQube quick-fixes (string literals, duplicated expressions, etc.), quedan **3 categorías de problemas arquitecturales** en el directorio wiring/:

| Problema | Instancias | Severidad SonarQube | Esfuerzo estimado |
|---|---|---|---|
| **Too many parameters** | 13 funciones | Major | 2-3 días (medio) |
| **High Cognitive Complexity** | 3 funciones (CC 21-98) | Critical | 3-5 días (alto) |
| **Unused facade re-exports** | 13 imports en wire_detail.py | Minor | 1 día (bajo) |

Estos NO son bugs — son **code smells** que afectan mantenibilidad. Todos son arreglables pero requieren refactoring arquitectural.

---

## 1. Too Many Parameters (13 funciones)

### 1.1 Descripción del problema

SonarQube marca funciones con >13 parámetros como violación. En Gradio wiring, cada widget de la UI es un parámetro individual:

```python
def wire_events(
    *,
    # Actor / meta (5 params)
    actor_id: gr.Textbox,
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    is_replicable: gr.Checkbox,
    generate_from_seed: gr.Number,
    # Armies (2 params)
    armies: gr.Textbox,
    army_points: gr.Number,
    # Table dimensions (4 params)
    table_preset: gr.Radio,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    # ... +120 parámetros más
) -> None:
    """Wire all event handlers."""
```

**Funciones afectadas** (params > 13):
- `wire_events` (134 params) — orquestador principal
- `wire_generate` (43 params)
- `wire_auth_events` (36 params)
- `_wire_create_scenario` (37 params)
- `wire_detail_page` (55 params)
- `wire_edit_button` (43 params)
- `wire_navigation` (22 params)
- `_add_or_update_deployment_zone_wrapper` (18 params)
- `wire_objectives` (18 params)
- `_add_or_update_scenography_wrapper` (17 params)
- `wire_favorites_page` (17 params)
- `wire_list_page` (18 params)
- `wire_home_page` (15 params)
- `build_zone_data` (15 params)
- `build_scenography_data` (15 params)

### 1.2 Causa raíz

**Arquitectura actual**: Gradio requiere referencias directas a widgets para `.change()`, `.click()`, etc. El call site (que crea los widgets) pasa cada uno como kwarg individual:

```python
# En create_scenario.py (call site)
wire_events(
    actor_id=actor_id_box,
    scenario_name=scenario_name_box,
    mode=mode_radio,
    # ... 131 más
)
```

Esto es explícito y type-safe (MyPy/Pylance validan cada kwarg), pero viola el límite de parámetros.

### 1.3 Soluciones propuestas

#### **Solución A: Dataclasses por sección** ⭐ Recomendada

**Concepto**: Agrupar widgets relacionados en dataclasses. El proyecto YA usa este patrón parcialmente en `_deployment/_context.py`:

```python
@dataclass
class DeploymentZonesCtx:
    """Widget references for deployment zones section."""
    toggle: gr.Checkbox
    group: gr.Group
    state: gr.State
    unit_state: gr.State
    # ... 25 widgets más
```

**Implementación completa**:

```python
# En ui/wiring/_refs.py (nuevo módulo)
from __future__ import annotations
from dataclasses import dataclass
import gradio as gr

@dataclass
class MetaWidgets:
    """Scenario metadata widgets."""
    actor_id: gr.Textbox
    scenario_name: gr.Textbox
    mode: gr.Radio
    is_replicable: gr.Checkbox
    generate_from_seed: gr.Number
    apply_seed_btn: gr.Button

@dataclass
class ArmiesWidgets:
    """Army configuration widgets."""
    armies: gr.Textbox
    army_points: gr.Number

@dataclass
class TableWidgets:
    """Table dimension widgets."""
    preset: gr.Radio
    width: gr.Number
    height: gr.Number
    unit: gr.Radio

@dataclass
class ObjectivesWidgets:
    """Objective points widgets."""
    toggle: gr.Checkbox
    group: gr.Group
    state: gr.State
    unit_state: gr.State
    description: gr.Textbox
    cx: gr.Number
    cy: gr.Number
    # ... resto
```

**Firma refactorizada**:

```python
def wire_events(
    *,
    # Secciones agrupadas (6 params en lugar de 134)
    meta: MetaWidgets,
    armies: ArmiesWidgets,
    table: TableWidgets,
    objectives: ObjectivesWidgets,
    deployment: DeploymentZonesCtx,  # Ya existe
    scenography: ScenographyCtx,      # Ya existe
) -> None:
    """Wire all event handlers."""
    # Acceso a widgets: meta.scenario_name, table.width, etc.
```

**Call site**:

```python
# En create_scenario.py
meta_widgets = MetaWidgets(
    actor_id=actor_id_box,
    scenario_name=scenario_name_box,
    mode=mode_radio,
    is_replicable=is_replicable_check,
    generate_from_seed=generate_from_seed_num,
    apply_seed_btn=apply_seed_btn,
)

wire_events(
    meta=meta_widgets,
    armies=armies_widgets,
    # ... solo 6 kwargs
)
```

**Pros**:
- ✅ Reduce params de 134 → ~6-10 (cumple con SonarQube)
- ✅ Type-safe completo (MyPy valida dataclass fields)
- ✅ Consistente con patrón existente (`DeploymentZonesCtx`, `ScenographyCtx`)
- ✅ Agrupa lógicamente widgets relacionados
- ✅ Fácil añadir/quitar campos sin cambiar firmas de 10 funciones

**Cons**:
- ❌ 2-3 días de refactoring (crear dataclasses + actualizar call sites)
- ❌ Call sites deben construir las dataclasses (más verboso en create_scenario.py)
- ❌ Necesita documentar el patrón para nuevos devs

**Esfuerzo**: MEDIO (2-3 días, ~15 dataclasses, 20 call sites)

---

#### **Solución B: TypedDicts** (alternativa)

Similar a dataclasses, pero usa TypedDicts (más flexible, menos type-safety en runtime):

```python
from typing import TypedDict

class MetaWidgets(TypedDict):
    actor_id: gr.Textbox
    scenario_name: gr.Textbox
    # ...

def wire_events(meta: MetaWidgets, ...) -> None:
    pass
```

**Pros**: Mismo beneficio que dataclasses, menos verboso en call sites (puedes pasar `{...}` directamente).  
**Cons**: MyPy type checking menos estricto, no hay validación en runtime.

---

#### **Solución C: `*args`, `**kwargs` pattern** ❌ NO recomendada

```python
def wire_events(**widgets: gr.Component) -> None:
    """All widgets passed as **kwargs."""
    actor_id = widgets["actor_id"]
    scenario_name = widgets["scenario_name"]
    # ...
```

**Pros**: Reduce params a 1.  
**Cons**: **Pierdes completamente type checking**. MyPy no puede validar si falta un widget. Errores solo en runtime. NO hacer.

---

#### **Solución D: Registry pattern** (over-engineered)

Crear un `WidgetRegistry` global que centralice todas las referencias:

```python
registry = WidgetRegistry()
registry.register("meta.actor_id", actor_id_box)
# ...
wire_events(registry=registry)
```

**Pros**: Máxima flexibilidad.  
**Cons**: Complejidad innecesaria, debugging difícil, anti-pattern para type checking. NO hacer.

---

### 1.4 Recomendación

**Solución A (Dataclasses)** es la mejor opción:
1. Consistente con código existente (`DeploymentZonesCtx`)
2. Type-safe
3. Cumple con SonarQube (13 params → 6-10 params)
4. Mejora mantenibilidad (cambios en una sección no afectan otras)

**Plan de implementación**:
1. Crear `ui/wiring/_refs.py` con todas las dataclasses (1 día)
2. Refactorizar `wire_events` y call sites (1 día)
3. Aplicar a otras 12 funciones (1 día)
4. Tests: Verificar que 2921 pasan (continuo)

---

## 2. High Cognitive Complexity (3 funciones)

### 2.1 Descripción del problema

SonarQube mide **Cognitive Complexity** (CC) — número de "decisiones" (if/for/while/and/or) que debe rastrear un humano al leer el código. Límite: **CC ≤ 15**.

**Funciones afectadas**:
- `wire_edit_button` — **CC 98** 🔴 CRÍTICO
- `wire_detail_page` — **CC 32** 🟠 Alto
- `wire_events` — **CC 21** 🟡 Medio

### 2.2 Causa raíz

Estas son **funciones orquestadoras** que hacen demasiado:
1. Mapean eventos de N widgets
2. Construyen payloads complejos
3. Lógica condicional inline (if X then update Y else update Z)
4. Anidamiento de callbacks

**Ejemplo — `wire_edit_button` (CC 98)**:

```python
def wire_edit_button(  # noqa: C901
    *,
    fetch_card_and_svg: Any,
    detail_edit_btn: gr.Button,
    # ... 41 parámetros más
) -> None:
    """Wire the Edit button to populate form from existing card."""

    def _on_edit_btn_click(card_id: str, actor_id: str | None) -> dict:
        if not card_id:
            return {output: {"status": "error", ...}}
        
        # Fetch card (10 líneas)
        card_data = fetch_card_and_svg(card_id, actor_id)
        if "error" in card_data:
            return {output: {"status": "error", ...}}
        
        # Parse scenario (15 líneas)
        scenario = card_data.get("scenario")
        if not scenario:
            return {output: {"status": "error", ...}}
        
        # Map meta fields (20 líneas)
        updates = {}
        updates[scenario_name] = scenario.get("name", "")
        updates[mode] = scenario.get("mode", "solo")
        if scenario.get("seed"):
            updates[seed_field] = scenario["seed"]
        # ... +50 líneas de mapeo
        
        # Map armies (15 líneas)
        armies_list = scenario.get("armies", [])
        updates[armies_textbox] = format_armies(armies_list)
        
        # Map objectives (30 líneas)
        obj_state = _api_objectives_to_state(scenario.get("objectives", []))
        updates[objectives_state] = obj_state
        updates[objectives_dropdown] = build_choices(obj_state)
        
        # Map deployment (30 líneas)
        # Map scenography (30 líneas)
        # Map special rules (30 líneas)
        
        # Switch to edit page (10 líneas)
        updates[page_state] = "edit"
        for i, col in enumerate(page_containers):
            updates[col] = gr.update(visible=(i == 2))
        
        return updates
    
    detail_edit_btn.click(
        fn=_on_edit_btn_click,
        inputs=[detail_card_id_state, actor_id_state],
        outputs=[...],  # 50+ outputs
    )
```

**Problemas**:
- Lógica de mapeo inline (debería estar en `_detail/_edit_logic.py`)
- 15 condiciones anidadas
- 200+ líneas en una sola función callback
- Mezcla de concerns (fetching, parsing, mapping, UI updates)

### 2.3 Soluciones propuestas

#### **Solución A: Extract Method** ⭐ Recomendada

**Patrón**: Ya aplicado parcialmente en `_deployment/`, `_detail/`, `_generate/`. Extender para cubrir toda la lógica:

**Nueva estructura** — `_detail/_edit_logic.py`:

```python
"""Pure logic for populating edit form from existing card."""

from __future__ import annotations
from typing import Any

def validate_edit_card_data(card_data: dict[str, Any]) -> tuple[dict | None, str | None]:
    """Validate fetched card data. Returns (scenario, error_msg)."""
    if "error" in card_data:
        return None, card_data.get("message", "Failed to fetch card")
    
    scenario = card_data.get("scenario")
    if not scenario:
        return None, "Card has no scenario data"
    
    return scenario, None


def map_scenario_to_form_meta(scenario: dict[str, Any]) -> dict[str, Any]:
    """Extract meta fields (name, mode, seed, etc.) from scenario."""
    return {
        "name": scenario.get("name", ""),
        "mode": scenario.get("mode", "solo"),
        "seed": scenario.get("seed"),
        "is_replicable": scenario.get("is_replicable", False),
        "armies_text": format_armies(scenario.get("armies", [])),
        "army_points": scenario.get("army_points", 500),
    }


def map_scenario_to_form_table(scenario: dict[str, Any]) -> dict[str, Any]:
    """Extract table dimensions from scenario."""
    map_spec = scenario.get("map_spec", {})
    return {
        "width": map_spec.get("width_cm", 120),
        "height": map_spec.get("height_cm", 120),
        "preset": "custom",  # Assume custom if explicit dimensions
    }


def map_scenario_to_form_objectives(scenario: dict[str, Any]) -> list[dict]:
    """Convert API objectives to UI state format."""
    from ._converters import _api_objectives_to_state
    return _api_objectives_to_state(scenario.get("objectives", []))

# Similarmente: map_*_deployment, map_*_scenography, map_*_special_rules
```

**`wire_edit_button` refactorizado** (CC 98 → **CC ~10**):

```python
def wire_edit_button(
    *,
    fetch_card_and_svg: Any,
    detail_edit_btn: gr.Button,
    # ... resto de params
) -> None:
    """Wire the Edit button to populate form from existing card."""

    def _on_edit_btn_click(card_id: str, actor_id: str | None) -> dict:
        # 1. Fetch card
        if not card_id:
            return _build_error(output, "No card selected")
        
        card_data = fetch_card_and_svg(card_id, actor_id)
        
        # 2. Validate
        scenario, err = validate_edit_card_data(card_data)
        if err:
            return _build_error(output, err)
        
        # 3. Map to form sections (delega a helpers puros)
        meta = map_scenario_to_form_meta(scenario)
        table = map_scenario_to_form_table(scenario)
        objectives = map_scenario_to_form_objectives(scenario)
        deployment = map_scenario_to_form_deployment(scenario)
        scenography = map_scenario_to_form_scenography(scenario)
        special_rules = map_scenario_to_form_special_rules(scenario)
        
        # 4. Build Gradio updates
        return _build_edit_form_updates(
            meta=meta,
            table=table,
            objectives=objectives,
            deployment=deployment,
            scenography=scenography,
            special_rules=special_rules,
            page_state=page_state,
            page_containers=page_containers,
            # ... widget refs
        )
    
    detail_edit_btn.click(
        fn=_on_edit_btn_click,
        inputs=[detail_card_id_state, actor_id_state],
        outputs=[...],
    )
```

**Helpers adicionales**:

```python
# En _detail/_ui_updates.py (nuevo o extender existente)
def _build_edit_form_updates(
    *,
    meta: dict,
    table: dict,
    objectives: list,
    # ... resto de secciones
    page_state: gr.State,
    page_containers: list[gr.Column],
    # ... widget refs (o usar dataclasses de Solución 1A)
) -> dict[Any, Any]:
    """Build Gradio gr.update() dict for all form widgets."""
    updates = {}
    
    # Meta
    updates[scenario_name_widget] = gr.update(value=meta["name"])
    updates[mode_widget] = gr.update(value=meta["mode"])
    # ...
    
    # Objectives
    updates[objectives_state] = objectives
    updates[objectives_dropdown] = gr.update(choices=get_choices(objectives))
    
    # Page navigation
    updates[page_state] = "edit"
    for i, col in enumerate(page_containers):
        updates[col] = gr.update(visible=(i == 2))
    
    return updates


def _build_error(output_widget: gr.JSON, message: str) -> dict:
    """Build error response for edit flow."""
    return {output_widget: {"status": "error", "message": message}}
```

**Resultado**:
- `wire_edit_button`: CC 98 → **CC 8-12** ✅
- `_on_edit_btn_click`: 200 líneas → **30 líneas** (orchestration pura)
- Lógica de mapeo: **100% testeable** (pure functions en `_edit_logic.py`)
- Tests unitarios: Pueden testear cada `map_*` por separado sin Gradio

**Pros**:
- ✅ Reduce CC drásticamente (98 → ~10)
- ✅ **100% testeable** — pure functions sin Gradio dependency
- ✅ Reusable — `map_scenario_to_form_*` útil en otros flujos
- ✅ Consistente con patrón existente (`_deployment/`, `_scenography/`)
- ✅ Separa concerns (fetching / validation / mapping / UI)

**Cons**:
- ❌ 3-5 días de refactoring (wire_edit_button es complejo)
- ❌ Necesita crear 10+ helpers nuevos
- ❌ Requiere tests nuevos para cada helper

**Esfuerzo**: ALTO (3-5 días)

---

#### **Solución B: Early returns + guard clauses**

Reducir anidamiento con early returns:

**Antes** (CC +3 por anidamiento):
```python
if card_id:
    card_data = fetch(card_id)
    if "error" not in card_data:
        scenario = card_data.get("scenario")
        if scenario:
            # ... 100 líneas
```

**Después** (CC -2):
```python
if not card_id:
    return _error("No card")

card_data = fetch(card_id)
if "error" in card_data:
    return _error(card_data["message"])

scenario = card_data.get("scenario")
if not scenario:
    return _error("No scenario data")

# ... lógica sin anidamiento
```

**Impacto**: Reduce CC en ~10-20%, pero NO suficiente para pasar de CC 98 → 15. Complementario a Solución A.

---

#### **Solución C: State machine pattern** (over-engineered)

Para `wire_events` con CC 21, podría modelarse como state machine:

```python
class EventWiringStateMachine:
    def wire_meta_events(self): ...
    def wire_table_events(self): ...
    # ...
```

**Pros**: Máxima separación.  
**Cons**: Over-engineering para el caso actual. NO recomendado hasta que CC supere 50.

---

### 2.4 Recomendación

**Solución A (Extract Method)** es la mejor:
1. Ya hay precedente en el proyecto (`_deployment/_form_state.py`, `_zone_builder.py`, etc.)
2. Reduce CC de 98 → ~10 (cumple SonarQube)
3. **Mejora testing** — pure functions sin Gradio
4. Mantenible — cambios en lógica de mapeo no tocan wire functions

**Plan de implementación** (5 etapas, 1 por función):
1. **wire_edit_button** (CC 98 → 10) — 2 días:
   - Crear `_detail/_edit_logic.py` con 6-8 helpers puros
   - Crear `_detail/_ui_updates.py` / extender existente
   - Refactorizar `_on_edit_btn_click` a orchestration mínima
   - Tests: 10-15 nuevos tests unitarios para helpers

2. **wire_detail_page** (CC 32 → 12) — 1 día:
   - Ya tiene `_detail/_render.py` — complementar con helpers de navegación
   - Extraer lógica de reload/refresh a `_detail/_reload_logic.py`

3. **wire_events** (CC 21 → 15) — 1 día:
   - Extraer orchestration de secciones a `_events/_meta_wiring.py`, etc.
   - Reducir anidamiento con early returns

4. **Verificar tests** — continuo
5. **Documentar patrón** — 0.5 días

---

## 3. Unused Facade Re-exports (13 imports)

### 3.1 Descripción del problema

En `wire_detail.py`:

```python
from adapters.ui_gradio.ui.wiring._detail._converters import (  # noqa: F401
    _api_deployment_to_state,
    _api_objectives_to_state,
    _api_scenography_to_state,
    _api_special_rules_to_state,
    _extract_objectives_text_for_form,
)
from adapters.ui_gradio.ui.wiring._detail._render import (  # noqa: F401
    _build_card_title,
    _extract_objectives_text,
    _field_row,
    _format_table_display,
    _render_detail_content,
    _render_mandatory_fields,
    _render_shared_with,
    _render_special_rules,
    _render_victory_points,
    _section_title,
)
```

**Problema**: Estos imports NO se usan en `wire_detail.py` — están ahí para que OTROS módulos puedan hacer:

```python
from adapters.ui_gradio.ui.wiring.wire_detail import _api_objectives_to_state
```

Esto es el **facade pattern** — `wire_detail.py` re-exporta símbolos de módulos internos (`_detail/`).

**SonarQube dice**: "Unused import" (no respeta `# noqa: F401` — eso es ruff/flake8).

### 3.2 Causa raíz

- `# noqa: F401` funciona en ruff/flake8/pylint (linters de Python)
- **SonarQube NO respeta `# noqa`** — tiene su propio motor de reglas
- El facade pattern es legítimo, pero SonarQube espera que los imports SE USEN en el archivo que los importa

### 3.3 Soluciones propuestas

#### **Solución A: Usar `__all__`** ⭐ Simple

Declarar explícitamente que estos son re-exports públicos:

```python
from adapters.ui_gradio.ui.wiring._detail._converters import (
    _api_deployment_to_state,
    _api_objectives_to_state,
    # ...
)

__all__ = [
    "_api_deployment_to_state",
    "_api_objectives_to_state",
    # ...
]
```

**Impacto**: SonarQube **podría** seguir quejándose (depende de su versión/config). `__all__` es la forma estándar de Python para indicar re-exports, pero SonarQube a veces ignora esto.

**Pros**: ✅ Estándar de Python, ✅ 5 minutos  
**Cons**: ❌ Puede no resolver el issue de SonarQube

---

#### **Solución B: Eliminar facade pattern** ⚠️ Cambio arquitectural

**Antes**:
```python
# En wire_edit_button.py
from adapters.ui_gradio.ui.wiring.wire_detail import _api_objectives_to_state
```

**Después**:
```python
# En wire_edit_button.py
from adapters.ui_gradio.ui.wiring._detail._converters import _api_objectives_to_state
```

Eliminar las líneas de re-export en `wire_detail.py`. Cada consumer importa directamente desde el módulo interno.

**Pros**: ✅ Sin imports "unused", ✅ Más explícito (ves de dónde viene cada función)  
**Cons**: ❌ Rompe el patrón facade (pérdida de abstracción), ❌ Imports más largos

**Esfuerzo**: BAJO (1 día — actualizar 20-30 imports en otros archivos)

---

#### **Solución C: Renombrar funciones (quitar underscore)** ⚠️ API breaking

Las funciones con `_` al inicio son "privadas" por convención. Si se van a re-exportar, hacerlas públicas:

**Antes**:
```python
# En _converters.py
def _api_objectives_to_state(...):
    """Convert API objectives..."""
```

**Después**:
```python
# En _converters.py
def api_objectives_to_state(...):  # Sin underscore
    """Convert API objectives..."""
```

**Pros**: ✅ Indica que son parte de la API pública del módulo  
**Cons**: ❌ Cambio de nombres en 50+ call sites, ❌ Conceptually son helpers internos

**Esfuerzo**: MEDIO (1 día)

---

#### **Solución D: Dummy reference en el facade**

Forzar que el import se "use" en `wire_detail.py`:

```python
from adapters.ui_gradio.ui.wiring._detail._converters import (
    _api_objectives_to_state,
    # ...
)

# Dummy reference para que SonarQube lo considere "usado"
_ = (
    _api_objectives_to_state,
    # ... resto de imports
)
```

**Pros**: ✅ Mantiene facade, ✅ 2 minutos  
**Cons**: ❌ Hack feo, ❌ Confuso para devs

---

### 3.4 Recomendación

**Prioridad**: BAJA — estos son "Minor" issues en SonarQube (no afectan funcionalidad).

**Opción preferida**:
1. **Solución A (`__all__`)** — probar primero (5 minutos)
2. Si SonarQube sigue quejándose → **Solución B (eliminar facade)** — más limpio que hacks

**Plan**:
- Añadir `__all__` a `wire_detail.py` (hoy, 5 min)
- Re-scan con SonarQube
- Si persiste → eliminar facade pattern (1 día)

---

## Resumen de prioridades

| Problema | Severidad | Esfuerzo | Prioridad | Impacto |
|---|---|---|---|---|
| **High CC** (wire_edit_button: 98) | 🔴 Critical | 2 días | ⭐⭐⭐ ALTA | +50 pure functions testeables |
| **High CC** (wire_detail_page: 32) | 🟠 Major | 1 día | ⭐⭐ Media | Mejora mantenibilidad |
| **High CC** (wire_events: 21) | 🟡 Major | 1 día | ⭐⭐ Media | Reduce complejidad |
| **Too many params** (13 funcs) | 🟠 Major | 2-3 días | ⭐⭐ Media | Mejor organización |
| **Facade re-exports** (13 imports) | 🟢 Minor | 5 min / 1 día | ⭐ Baja | Limpieza cosmética |

**Recomendación general**:
1. Empezar con **wire_edit_button** (CC 98 → 10) — mayor ROI: reduces Critical issue + ganas testing puro
2. Continuar con **Too many params** (dataclasses) — beneficio cross-cutting
3. Finalizar con **wire_detail_page / wire_events** (CC medio)
4. Facade re-exports al final (prioridad baja)

**Tiempo total**: 7-10 días para completar TODO (puede hacerse incremental).

---

## Notas de implementación

### Testing strategy
Para CADA refactoring:
1. Baseline: `pytest tests/ -q` → 2921 passed ✅
2. Refactorizar función X
3. Re-run: `pytest tests/ -q` → 2921 passed ✅
4. Si falla → rollback, investigar

### TDD approach (recomendado para Extract Method)
Para nuevos helpers puros (e.g., `map_scenario_to_form_meta`):
1. **RED**: Escribir test unitario que falla
2. **GREEN**: Implementar helper mínimo
3. **REFACTOR**: Limpiar, extraer constantes
4. Repetir

Ejemplo:
```python
# tests/unit/adapters/ui_gradio/ui/wiring/_detail/test_edit_logic.py
def test_map_scenario_to_form_meta_basic():
    scenario = {
        "name": "Epic Battle",
        "mode": "competitive",
        "seed": 12345,
    }
    result = map_scenario_to_form_meta(scenario)
    assert result["name"] == "Epic Battle"
    assert result["mode"] == "competitive"
    assert result["seed"] == 12345
```

### Ruff/MyPy compliance
- Todos los helpers deben pasar `ruff check`
- Type hints obligatorios (`def func(...) -> ReturnType:`)
- Docstrings mínimos (1 línea para helpers privados)

---

## Alternativas descartadas

### "No hacer nada"
**Justificación**: Estos son code smells, no bugs funcionales. 2921 tests pasan. ¿Por qué refactorizar?

**Contra-argumento**:
- **Deuda técnica**: CC 98 en `wire_edit_button` hace que sea casi inmodificable sin introducir bugs
- **Testing**: Lógica actualmente en wiring NO es unitariamente testeable (necesita Gradio mocks)
- **Mantenibilidad**: Añadir un campo nuevo requiere tocar 10+ archivos
- **Onboarding**: Nuevos devs tardan días en entender `wire_edit_button` de 200 líneas

**Veredicto**: Refactorizar wire_edit_button es CRÍTICO (CC 98 es técnicamente inmantenible). El resto es negociable.

### "Suprimir SonarQube warnings"
Configurar SonarQube para ignorar estos issues en `sonar-project.properties`:

```properties
sonar.issue.ignore.multicriteria=e1,e2
sonar.issue.ignore.multicriteria.e1.ruleKey=python:S107
sonar.issue.ignore.multicriteria.e1.resourceKey=**/*wire*.py
```

**Contra**: Oculta el problema, no lo resuelve. La deuda técnica sigue creciendo.

---

## Próximos pasos

1. **Decisión**: ¿Qué problema atacar primero? (Ver tabla de prioridades)
2. **Planning**: Crear issues/tasks para cada refactoring
3. **Implementación incremental**: Un problema a la vez, siempre con tests passing
4. **Documentación**: Actualizar `AGENTS.md` con nuevos patrones cuando se implementen

---

**Autor**: GitHub Copilot (Claude Sonnet 4.5)  
**Review**: Pendiente
