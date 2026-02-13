# Definition of Done (DoD)

Para dar algo por "hecho" en cualquier PR/feature:

## Tests
- [ ] Tests target en verde (unit/integration según alcance)
- [ ] Suite completa pasa (`pytest tests/unit tests/integration -q`)
- [ ] Todos los tests E2E pasan (si aplica): `pytest tests/e2e -q`
- [ ] Cobertura cumple policy:
  - domain/ → 100%
  - application/ + infrastructure/ → 80%
  - adapters/ → best-effort (60%+)

## Código
- [ ] Lint pasa: `ruff check src/ tests/`
- [ ] No imports `src.` nuevos (imports absolutos desde paquete)
- [ ] No lógica de negocio en adapters (solo wiring/mapping)
- [ ] Facades <450 líneas (ideal <350)
- [ ] Módulos internos (_*/) tienen tests dedicados (1:1)
- [ ] # noqa solo cuando es inevitable + comentario justificando
- [ ] Sin warnings de pytest (deprecations, etc.)

## Arquitectura
- [ ] Respeta capas (ver `context/architecture/layers.md`)
- [ ] Domain no importa application/infrastructure/adapters
- [ ] Application no importa infrastructure/adapters
- [ ] Infrastructure no importa adapters
- [ ] Composition root único: `infrastructure.bootstrap.build_services()`

## Seguridad
- [ ] Deny-by-default en nuevos endpoints
- [ ] Anti-IDOR: `actor_id` verificado en reads/writes
- [ ] Input validation: ValidationError en domain
- [ ] Error mapping: ValidationError → 400 en adapters
- [ ] Secrets no hard-coded (usar env vars)

## Documentación
- [ ] CHANGELOG.md actualizado (si cambio notable)
- [ ] Docstrings en funciones públicas/complejas
- [ ] APIs nuevas documentadas en AGENTS.md (si aplica)
- [ ] Context files actualizados (si hay cambio arquitectónico)

## Refactor específico (si aplica)
- [ ] Facade pattern:
  - [ ] Facade <450 líneas
  - [ ] Módulos internos 2-6 (sweet spot)
  - [ ] Cada interno tiene propósito único
  - [ ] Internos puros no importan gradio
  - [ ] 1 test file por módulo interno
  - [ ] Backward compatible (firma pública sin cambios)

## Checklist Rápido PR-Ready

```bash
# 1. Tests
pytest tests/unit tests/integration -q

# 2. Lint
ruff check src/ tests/

# 3. Cobertura (opcional local)
pytest --cov=src --cov-report=term-missing

# 4. Baseline check
# Confirmar que el número de tests pass >= baseline esperado
```

## Ejemplos de "Done"

### Caso 1: Nuevo use case
- ✅ Tests unit para DTO + execute()
- ✅ Tests integration con repo in-memory
- ✅ Tests E2E con Flask client
- ✅ Cobertura domain 100%, application 80%
- ✅ ruff clean
- ✅ CHANGELOG con entry

### Caso 2: Refactor facade (god-module split)
- ✅ Baseline tests pass (ej: 1473)
- ✅ Nuevos tests unit para internos (ej: +44)
- ✅ Total tests pass (ej: 1517)
- ✅ Facade <450 líneas
- ✅ ruff clean (fix I001/F401)
- ✅ Backward compatible (firma sin cambios)
- ✅ AGENTS.md actualizado con nuevo estado

### Caso 3: Fix bug
- ✅ Test que reproduce el bug (RED)
- ✅ Fix implementado (GREEN)
- ✅ Refactor si es necesario (REFACTOR)
- ✅ Suite completa pasa
- ✅ CHANGELOG con bugfix entry

## No-Gos (Bloquean Merge)

🚫 **Tests rojos** en cualquier suite  
🚫 **ruff errors** sin fixear  
🚫 **Imports `src.`** nuevos  
🚫 **Lógica de negocio en adapters**  
🚫 **Facades >500 líneas** sin plan de split  
🚫 **Cobertura domain <100%**  
🚫 **Secrets hard-coded**  
🚫 **Breaking changes** sin migración documentada  

Si alguno de estos aparece: **no merge**, regresa a fix.

## Referencias
- `context/quality/tdd.md` — RED/GREEN/REFACTOR cycle
- `context/quality/testing-strategy-60-30-10.md` — Distribución de tests
- `context/quality/coverage-policy-100-80-0.md` — Targets de cobertura
- `context/architecture/facade-pattern.md` — Patrón de refactor
- `context/security/security-by-design.md` — Principios de seguridad
