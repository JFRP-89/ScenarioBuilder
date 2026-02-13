# Patrón Facade + Módulos Internos

## Motivación

**Problema**: God-modules (500+ líneas) con múltiples responsabilidades dificultan testing, mantenimiento y legibilidad.

**Solución**: Facade pattern + paquetes internos con prefijo `_`.

## Estructura

```
wire_example.py          # Facade público (250-450 líneas)
_example/                # Paquete interno (no API pública)
├── __init__.py          # "Internal helpers — not a public API"
├── _logic.py            # Lógica pura (sin Gradio)
├── _ui_updates.py       # Helpers de gr.update()
├── _form_state.py       # Estado y conversiones de formularios
└── _builder.py          # Builders complejos (never-raise)
```

## Reglas de Diseño

### 1. Facade (wire_*.py)
- **Responsabilidad**: Wiring de eventos Gradio (`.click()`, `.change()`, etc.)
- **Tamaño objetivo**: <450 líneas; ideal <350 líneas
- **Importa de**: `_module_name/*` (sus helpers internos)
- **Delega todo**: Cada inner function llama a un helper extraído
- **Nunca**: Lógica compleja inline, validaciones manuales, loops anidados

### 2. Módulos Internos (_module_name/*)
- **Prefijo `_`**: Indica "internal use only"
- **Sin Gradio** (ideal): Lógica pura, fácil de testear
- **Con Gradio** (permitido): Solo para builders de `gr.update()` (ej: `_ui_updates.py`, `_resets.py`)
- **Organización típica**:
  - `_logic.py` / `_create_logic.py`: Validaciones puras, reglas de negocio
  - `_form_state.py`: Valores por defecto, conversiones de estado
  - `_ui_updates.py`: Builders de `gr.update(visible=..., value=...)`
  - `_converters.py`: API → UI state mappers
  - `_render.py`: HTML rendering (ej: detail content)
  - `_geometry.py`: Cálculos geométricos puros
  - `_polygon.py`: Parsers de coordenadas
  - `_builder.py`: Builders complejos (never-raise pattern)
  - `_outputs.py`: Tuple builders para outputs de Gradio
  - `_resets.py`: Form reset helpers
  - `_preview.py`: Preview + render delegators
  - `_zone_builder.py`: Domain-specific builders

### 3. Testing
- **1 test file por módulo interno**: `test_<facade>_<internal>.py`
- **Cobertura objetivo**: 80%+ en módulos internos (lógica pura fácil de testear)
- **Sin mocks de Gradio**: Los helpers puros no deben depender de Gradio
- **Fixtures ligeros**: Solo data structures, no componentes Gradio

## Ejemplo Real: wire_generate

### Antes (349 líneas, difícil de testear)
```python
def wire_generate(*, actor_id: gr.Textbox, ...):
    def _preview_and_render(*args):
        preview_data = handle_preview(*args)
        svg_html = render_svg_from_card(preview_data)
        return preview_data, svg_html
    
    def _on_create_scenario(preview_data, edit_id=""):
        # 80 líneas de validación + API calls + resets inline
        if not preview_data or not isinstance(preview_data, dict):
            return _stay("Generate a card preview first.")
        # ... más validaciones ...
        # ... form resets inline ...
        # ... dropdown resets inline ...
```

### Después (280 líneas facade + 4 módulos internos testables)

#### wire_generate.py (facade)
```python
from adapters.ui_gradio.ui.wiring._generate._preview import preview_and_render
from adapters.ui_gradio.ui.wiring._generate._create_logic import validate_preview_data
from adapters.ui_gradio.ui.wiring._generate._resets import build_form_resets, build_dropdown_resets
from adapters.ui_gradio.ui.wiring._generate._outputs import build_stay_outputs

def wire_generate(*, actor_id: gr.Textbox, ...):
    # Delega preview
    generate_btn.click(fn=preview_and_render, inputs=[...], outputs=[...])
    
    def _on_create_scenario(preview_data, edit_id=""):
        # Delega validación
        ok, err_msg = validate_preview_data(preview_data)
        if not ok:
            return _stay(err_msg)
        
        # ... lógica de negocio ...
        
        # Delega resets
        form_resets = build_form_resets()
        dropdown_resets = build_dropdown_resets(_dropdown_lists)
```

#### _generate/_create_logic.py (puro, testeable)
```python
def validate_preview_data(preview_data: Any) -> tuple[bool, str]:
    """Pure validation — no Gradio, no I/O."""
    if not preview_data or not isinstance(preview_data, dict):
        return False, "Generate a card preview first."
    if preview_data.get("status") == "error":
        return False, f"Error: {preview_data.get('message')}"
    if preview_data.get("status") != "preview":
        return False, "Generate a card preview first."
    return True, ""
```

#### Tests (44 tests, 100% cobertura de lógica)
```python
# tests/unit/adapters/ui_gradio/ui/wiring/test_generate_create_logic.py
def test_valid_preview():
    ok, msg = validate_preview_data({"status": "preview", "name": "Battle"})
    assert ok is True
    assert msg == ""

def test_error_with_message():
    ok, msg = validate_preview_data({"status": "error", "message": "Invalid seed"})
    assert ok is False
    assert msg == "Error: Invalid seed"
```

## Casos de Uso Completados

### 1. wire_detail → _detail/ (2 módulos)
- **Problema**: 400+ líneas, mezclaba rendering con conversión de estado
- **Solución**:
  - `_render.py`: HTML rendering puro
  - `_converters.py`: API → UI state mappers
- **Resultado**: 45 tests, facade 350 líneas

### 2. wire_deployment_zones → _deployment/ (4 módulos)
- **Problema**: 713 líneas, geometría + UI updates + form state
- **Solución**:
  - `_form_state.py`: Defaults y selected state
  - `_geometry.py`: Cálculos puros (intersections, areas)
  - `_ui_updates.py`: gr.update() builders
  - `_zone_builder.py`: Domain builder (never-raise)
- **Resultado**: 83 tests, facade 426 líneas

### 3. wire_scenography → _scenography/ (4 módulos)
- **Problema**: 713 líneas, parsing de polígonos + conversiones + builders
- **Solución**:
  - `_form_state.py`: Estado por defecto
  - `_polygon.py`: Parse/conversion de coordenadas (noqa: C901)
  - `_ui_updates.py`: Visibility helpers
  - `_builder.py`: Never-raise builder (noqa: C901)
- **Resultado**: 71 tests, facade 426 líneas

### 4. wire_generate → _generate/ (4 módulos)
- **Problema**: 349 líneas, preview + validación + create + resets
- **Solución**:
  - `_preview.py`: Delegation a services
  - `_create_logic.py`: Validación pura
  - `_resets.py`: Form/dropdown/extra reset builders
  - `_outputs.py`: Stay-on-page tuple builder
- **Resultado**: 44 tests, facade 280 líneas

## Beneficios Medidos

| Métrica | Antes (ejemplo) | Después |
|---------|----------------|---------|
| Líneas facade | 713 | 280-450 |
| Complejidad ciclomática | 15-20 | 5-10 |
| Tests unitarios | 0-5 | 40-80 |
| Cobertura lógica pura | <50% | >90% |
| Tiempo de comprensión | ~30min | ~10min |

## Anti-Patrones a Evitar

### ❌ No extraer helpers que solo se usan una vez
```python
# Innecesario
def _single_use_helper():
    return x + 1

def main():
    result = _single_use_helper()  # Solo usado aquí
```

### ❌ No sobre-fragmentar (módulos de <20 líneas)
```python
# Excesivo
_add.py         # def add(a, b): return a + b
_subtract.py    # def subtract(a, b): return a - b
```

### ❌ No mezclar Gradio en módulos de lógica pura
```python
# Mal
def validate_form(name: str, mode_widget: gr.Radio) -> bool:
    mode = mode_widget.value  # Acopla a Gradio
```

### ✅ Bien
```python
def validate_form(name: str, mode: str) -> bool:
    return bool(name) and mode in ["casual", "matched"]
```

## Workflow de Refactor

1. **Baseline**: Confirmar tests en verde + ruff clean
2. **Audit**: Identificar clusters (lógica, UI, estado, conversiones)
3. **Extract**: Un módulo a la vez, empezar con lo más puro
4. **Test**: Crear tests para cada módulo extraído
5. **Facade**: Reescribir original como delegator
6. **Verify**: `pytest` + `ruff` green
7. **Iterate**: Siguiente cluster

## Checklist de Calidad

- [ ] Facade <450 líneas (ideal <350)
- [ ] Cada módulo interno tiene propósito único
- [ ] Módulos puros no importan `gradio`
- [ ] 1 test file por módulo interno
- [ ] Cobertura >80% en módulos puros
- [ ] Todos los tests pasan (baseline + nuevos)
- [ ] `ruff check` clean (fix I001/F401)
- [ ] `# noqa: C901` solo en funciones complejas inevitables
- [ ] __init__.py en cada paquete interno marca como "not public API"
- [ ] Firma pública del facade sin cambios (backward compatible)

## Decisiones de Diseño

### ¿Cuándo extraer?
- Facade >500 líneas
- >3 responsabilidades distintas
- Lógica difícil de testear inline

### ¿Cuántos módulos internos?
- **2-6 módulos**: Sweet spot
- <2: Probablemente no vale la pena
- >8: Puede ser sobre-ingeniería

### ¿Qué nombre dar?
- Prefijo `_` siempre
- Nombre descriptivo de responsabilidad única:
  - `_logic` / `_create_logic`: Validación/reglas
  - `_form_state`: Estado de formularios
  - `_ui_updates`: Builders de gr.update()
  - `_converters`: Mappers API↔UI
  - `_render`: HTML generation
  - `_geometry` / `_polygon`: Cálculos específicos
  - `_builder`: Domain builders complejos
  - `_outputs` / `_resets` / `_preview`: Helpers específicos

### ¿# noqa: C901?
- Solo para funciones complejas inevitables (ej: parsers, builders con muchos casos)
- Documentar por qué la complejidad es necesaria
- Preferir simplificar antes que noqa
