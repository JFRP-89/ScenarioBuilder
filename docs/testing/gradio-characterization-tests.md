# Characterization Tests for Gradio UI Adapter

## Resumen

Se han creado **characterization tests** completos para congelar el comportamiento actual del Gradio UI adapter **SIN refactorizar**, permitiendo refactorización segura en el futuro.

## Tests Creados

### Tests Unitarios (110 tests)

#### 1. `test_unit_conversions.py` (24 tests)
Congela comportamiento de helpers de conversión de unidades:
- `_convert_to_cm()` - Conversión a centímetros (cm/in/ft)
- `_convert_from_cm()` - Conversión desde centímetros
- `_convert_unit_to_unit()` - Conversión entre unidades con redondeo
- `_build_custom_table_payload()` - Validación de dimensiones custom (60-300cm)

**Casos cubiertos:**
- Conversiones básicas (cm ↔ in ↔ ft)
- Redondeo a 2 decimales
- Validación de límites (min 60cm, max 300cm)
- Manejo de valores inválidos (≤0, fuera de rango)

#### 2. `test_parsing_helpers.py` (24 tests)
Congela comportamiento de helpers de parsing de texto/JSON:
- `_parse_json_list()` - Parser genérico con validación de tipo
- `_parse_deployment_shapes()` - Max 2 shapes, require type
- `_parse_map_specs()` - Sin límite, require type
- `_build_shared_with_list()` - Parse CSV de user IDs

**Casos cubiertos:**
- JSON válido/inválido
- Límites (max_len)
- Validación de campos requeridos (type)
- Whitespace stripping
- Empty strings → []

#### 3. `test_special_rules_helpers.py` (25 tests)
Congela comportamiento de helpers de special rules state:
- `_validate_special_rules()` - Validación con errores indexados
- `_add_special_rule()` - Agregar regla con UUID único
- `_remove_last_special_rule()` - Remover última regla

**Casos cubiertos:**
- Validación de campos (name, rule_type, value)
- Normalización (description vs source)
- Inmutabilidad (no muta estado original)
- Mensajes de error con índice 1-based

#### 4. `test_payload_ui_helpers.py` (27 tests)
Congela comportamiento de helpers de payload y UI:
- `_build_generate_payload()` - Payload con mode/seed
- `_apply_table_config()` - Config de tabla (preset vs custom)
- `_apply_optional_text_fields()` - Agregar campos opcionales
- `_on_table_preset_change()` - Auto-fill dimensiones al cambiar preset
- `_on_table_unit_change()` - Convertir + clamp al cambiar unidad

**Casos cubiertos:**
- Seed falsy (0 → None)
- Preset standard/massive auto-fill
- Unit conversion con clamping a límites
- Whitespace stripping
- gr.update() retorna dict

#### 5. `test_validation.py` (10 tests existentes)
Tests previos de `_validate_required_fields()`:
- Validación de campos mandatory
- Mensajes de error detallados

### Tests de Integración (11 tests)

#### `test_gradio_app_smoke.py` (ampliado)

**TestImportDoesNotCallRequests (1 test):**
- ✅ Import no hace HTTP calls

**TestBuildAppReturnsBlocks (1 test):**
- ✅ build_app() retorna gr.Blocks sin HTTP calls

**TestGetApiBaseUrl (5 tests):**
- ✅ Lee env var API_BASE_URL
- ✅ Normaliza: strip trailing slash(es)
- ✅ Preserva URL sin trailing slash
- ✅ Default cuando env var falta
- ✅ Siempre retorna URL sin trailing slash

**TestBuildHeaders (4 tests):**
- ✅ Retorna dict con X-Actor-Id
- ✅ Maneja actor_id vacío
- ✅ Maneja actor_id complejo (email)
- ✅ Cada llamada retorna dict nuevo

## Resultados

```bash
$ pytest tests/unit/adapters/ui_gradio/ tests/integration/adapters/ui_gradio/ -v --cov=src/adapters/ui_gradio
```

**121 tests pasando** ✅
- 110 tests unitarios
- 11 tests de integración
- 45% cobertura en app.py (helpers puros tienen ~100%, UI wiring sin cubrir por diseño)

## Comandos para Ejecutar Tests

### Todos los tests del Gradio adapter
```bash
pytest tests/unit/adapters/ui_gradio/ tests/integration/adapters/ui_gradio/ -v
```

### Con coverage
```bash
pytest tests/unit/adapters/ui_gradio/ tests/integration/adapters/ui_gradio/ --cov=src/adapters/ui_gradio --cov-report=term-missing
```

### Solo tests unitarios
```bash
pytest tests/unit/adapters/ui_gradio/ -v
```

### Solo tests de integración
```bash
pytest tests/integration/adapters/ui_gradio/ -v
```

### Test específico
```bash
pytest tests/unit/adapters/ui_gradio/test_unit_conversions.py -v
pytest tests/unit/adapters/ui_gradio/test_parsing_helpers.py -v
pytest tests/unit/adapters/ui_gradio/test_special_rules_helpers.py -v
pytest tests/unit/adapters/ui_gradio/test_payload_ui_helpers.py -v
```

## Beneficios

1. **Safety net para refactoring**: 121 tests congelan comportamiento actual
2. **Documentación ejecutable**: Tests describen comportamiento esperado
3. **Detección de regresiones**: Cualquier cambio que rompa comportamiento fallará
4. **Confianza para refactorizar**: Saber exactamente qué se rompió y dónde
5. **Monkeypatch HTTP**: Garantía de que build_app() NO hace HTTP calls

## Hallazgos Documentados

Durante la creación de tests, se documentaron estos comportamientos actuales:

1. **Seed=0 es falsy**: `int(seed) if seed else None` convierte 0 → None
2. **gr.update() retorna dict**: No es objeto con atributo `.visible`
3. **Trailing slash normalization**: API_BASE_URL siempre sin trailing slash
4. **Custom table limits**: 60-300 cm (validación en payload builder)
5. **Special rules**: Validación retorna tuple (normalized, error)
6. **State immutability**: Helpers no mutan estado original (usan spread)

## Próximos Pasos

Ahora es **seguro refactorizar** el Gradio adapter con estos characterization tests como safety net:
- Extraer funciones puras a módulos separados
- Simplificar lógica compleja
- Reducir complejidad ciclomática
- Mejorar nombres de funciones
- **Los tests indicarán si algo se rompe**

## Archivos Modificados

**Nuevos archivos:**
- `tests/unit/adapters/ui_gradio/test_unit_conversions.py`
- `tests/unit/adapters/ui_gradio/test_parsing_helpers.py`
- `tests/unit/adapters/ui_gradio/test_special_rules_helpers.py`
- `tests/unit/adapters/ui_gradio/test_payload_ui_helpers.py`

**Archivos ampliados:**
- `tests/integration/adapters/ui_gradio/test_gradio_app_smoke.py` (+7 tests)

**No modificado:**
- `src/adapters/ui_gradio/app.py` (comportamiento congelado, listo para refactor)
