# God-Module / God-Class Audit — `src/`

> Generado: 2026-02-12 · Branch: `ui/alpha.0.2`  
> Baseline: 1191 tests passing · ruff clean

## Módulos ya refactorizados (PR4)

| Módulo original | Líneas antes → después | Paquete interno |
|---|---|---|
| `state_helpers.py` | 949 → 118 (facade) | `_state/` (7 módulos) |
| `svg_map_renderer.py` | 673 → ~200 (facade + delegates) | `_renderer/` (3 módulos) |
| `generate.py` | 560 → 324 (facade) | `_generate/` (2 módulos) |

---

## Auditoría completa de archivos restantes

| # | Archivo | Líneas | Defs | Cohesión | Veredicto |
|---|---------|-------:|-----:|----------|-----------|
| 1 | `ui/wiring/wire_deployment_zones.py` | 960 | 14 | Media | **SPLIT** |
| 2 | `ui/wiring/wire_detail.py` | 993 | 28 | Baja | **SPLIT** |
| 3 | `ui/wiring/wire_scenography.py` | 757 | 11 | Alta | BORDERLINE |
| 4 | `app.py` | 685 | 1 | Alta | SKIP |
| 5 | `builders/payload.py` | 444 | 7 | Media | BORDERLINE |
| 6 | `handlers.py` | 435 | 14 | Baja | **SPLIT** |
| 7 | `ui/wiring/__init__.py` | 360 | 1 | Alta | SKIP |
| 8 | `use_cases/generate_scenario_card.py` | 390 | 10 | Alta | SKIP |
| 9 | `ui/wiring/wire_objectives.py` | 296 | ~8 | Alta | SKIP |
| 10 | `http_flask/routes/cards.py` | 266 | 8 | Alta | SKIP |
| 11 | `ui/wiring/wire_favorites.py` | 246 | ~8 | Alta | SKIP |
| 12 | `ui/wiring/wire_special_rules.py` | 230 | ~8 | Alta | SKIP |
| 13 | `domain/maps/table_size.py` | 226 | 15 | Alta | SKIP |
| 14 | `ui/wiring/wire_list.py` | 226 | ~8 | Alta | SKIP |

---

## Detalle de candidatos a split

### P1 — `wire_detail.py` (993 líneas, 28 funciones) → **SPLIT**

Tres grupos claramente separables con **cero acoplamiento** entre ellos:

| Grupo | Líneas aprox. | Contenido | Dependencia de Gradio |
|-------|-------------:|-----------|----------------------|
| **A — HTML rendering** | ~225 | `_field_row`, `_section_title`, `_render_shared_with`, `_render_victory_points`, `_render_special_rules`, `_format_table_display`, `_render_mandatory_fields`, `_render_detail_content`, `_build_card_title`, `_wrap_svg` | Ninguna |
| **B — API→UI converters** | ~165 | `_extract_objectives_text_for_form`, `_api_special_rules_to_state`, `_api_deployment_to_state`, `_api_scenography_to_state`, `_api_objectives_to_state` | Ninguna |
| **C — Wiring** | ~500 | `wire_detail_page`, `_wire_edit_button`, closures | Sí |

**Split propuesto:**
```
ui/wiring/_detail/
  __init__.py
  _render.py        ← Grupo A (funciones puras de HTML)
  _converters.py    ← Grupo B (transformadores API→state)
wire_detail.py      ← Facade: importa A y B, conserva C
```

**Valor:** Mayor split de la auditoría. Cada grupo es testeable de forma independiente.

---

### P2 — `handlers.py` (435 líneas, 14 funciones) → **SPLIT**

Cuatro grupos sin dependencias cruzadas (grab-bag de funciones puras):

| Grupo | funciones | Líneas aprox. |
|-------|----------|-------------:|
| **Table handlers** | `on_table_preset_change`, `on_table_unit_change`, `update_objective_defaults` | ~90 |
| **Visibility toggles** | `toggle_section`, `toggle_scenography_forms`, `update_shared_with_visibility` | ~45 |
| **Special Rules handlers** | `add_special_rule`, `remove_last_special_rule`, `remove_selected_special_rule` | ~110 |
| **VP + misc handlers** | `add_victory_point`, `remove_last_victory_point`, `remove_selected_victory_point`, `on_polygon_preset_change` | ~150 |

**Split propuesto:**
```
handlers/
  __init__.py       ← Facade re-exports
  _table.py
  _toggles.py
  _special_rules.py
  _victory_points.py
```

---

### P3 — `wire_deployment_zones.py` (960 líneas, 14 funciones) → **SPLIT**

| Grupo | Líneas aprox. | Contenido | Dependencia de Gradio |
|-------|-------------:|-----------|----------------------|
| **Geometry calculators** | ~105 | `_calculate_triangle_vertices`, `_calculate_circle_vertices` | Ninguna (puro `math`) |
| **Zone CRUD closures** | ~455 | `_build_error_result`, `_on_zone_selected`, `_cancel_edit_zone`, `_add_or_update_deployment_zone_wrapper` | Sí (widgets) |
| **UI toggle/change closures** | ~325 | `_on_zone_border_or_fill_change`, `_on_zone_type_change`, `_on_perfect_triangle_change`, bindings | Sí (widgets) |

**Split propuesto:**
```
ui/wiring/_deployment/
  __init__.py
  _geometry.py      ← Calculadoras de triángulo/círculo (funciones puras)
wire_deployment_zones.py  ← Facade: importa geometry, conserva wiring
```

**Nota:** Los closures CRUD y UI comparten scope de widgets, por lo que separarlos requiere refactorizar las references. El valor principal está en extraer la geometría pura.

---

## Candidatos BORDERLINE (diferir salvo crecimiento)

### P4 — `wire_scenography.py` (757 líneas, 11 funciones)

Un solo `wire_scenography()` con closures acoplados a widgets. El bulk viene de `_add_or_update_scenography_wrapper` (~260 líneas de validación + parsing de polígonos) y `_on_scenography_selected` (~135 líneas). Separable si se pasan widgets como parámetros, pero el ROI es bajo.

### P5 — `builders/payload.py` (444 líneas, 7 funciones)

Dos sub-responsabilidades: **building** (`build_generate_payload`, `apply_table_config`, `apply_optional_text_fields`, `apply_special_rules`, `apply_visibility`) y **validation** (`validate_victory_points`, `validate_required_fields`). Separar en `payload_build.py` + `payload_validate.py` si crece.

---

## Archivos descartados (SKIP)

| Archivo | Razón |
|---------|-------|
| `app.py` (685 líneas) | Composition root — 1 función, complejidad inherente de ensamblaje |
| `wiring/__init__.py` (360 líneas) | Dispatcher puro — forwarding de parámetros |
| `generate_scenario_card.py` (390 líneas) | Use case limpio: Request DTO + Response DTO + `.execute()` |
| `wire_objectives.py` (296 líneas) | Cohesivo, tamaño aceptable |
| `routes/cards.py` (266 líneas) | Cohesivo, tamaño aceptable |
| `wire_favorites.py` (246 líneas) | Cohesivo, tamaño aceptable |
| `wire_special_rules.py` (230 líneas) | Cohesivo, tamaño aceptable |
| `table_size.py` (226 líneas) | 1 clase + helpers de dominio, cohesivo |
| `wire_list.py` (226 líneas) | Cohesivo, tamaño aceptable |

---

## Resumen ejecutivo

| Prioridad | Archivo | Acción | Reducción esperada |
|-----------|---------|--------|-------------------|
| **P1** | `wire_detail.py` | Split en `_detail/_render.py` + `_detail/_converters.py` + facade | Facade baja a ~500 líneas |
| **P2** | `handlers.py` | Split en `handlers/` package (4 módulos) | Cada módulo ~80–130 líneas |
| **P3** | `wire_deployment_zones.py` | Extraer geometría pura a `_geometry.py` | Archivo baja a ~850 líneas |
| P4 | `wire_scenography.py` | Diferir salvo crecimiento | — |
| P5 | `payload.py` | Diferir salvo crecimiento | — |

**Total candidatos firmes: 3 archivos (P1–P3)**  
**Total borderline: 2 archivos (P4–P5)**  
**Archivos que no requieren acción: 9**
