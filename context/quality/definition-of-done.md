# Definition of Done (DoD)

Para dar algo por "hecho" en cualquier PR/feature:

## Tests
- [ ] Tests target en verde (unit/integration según alcance)
- [ ] Suite completa pasa: `pytest tests/unit tests/integration -q` (1972+ unit tests)
- [ ] Todos los tests E2E pasan (si aplica): `pytest tests/e2e -q` (100+ tests)
- [ ] Cobertura cumple policy **obligatorio en toda PR**:
  - domain/ → **100%** (738+ statements) REQUIRED
  - application/ → ≥**80%** (820+ statements) REQUIRED
  - infrastructure/adapters/ → best-effort (pragmatic)

## Code Quality Gates (REQUIRED — 0 tolerance)
- [ ] Lint limpio: `ruff check src/ tests/` → 0 errors
- [ ] Formato compliant: `black --check src/ tests/` → all files compliant
- [ ] Type safety: `mypy src/ --ignore-missing-imports` → 0 issues (205+ src files)
- [ ] Security SAST: `bandit -r src/domain -q` → 0 issues in domain REQUIRED
- [ ] Type checking on tests: `mypy tests/ --ignore-missing-imports` → 0 issues (160+ test files)

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
# 1. Quality gates (REQUIRED — must all pass)
ruff check src/ tests/                          # 0 errors
black --check src/ tests/                       # all compliant
mypy src/ --ignore-missing-imports              # 0 issues
mypy tests/ --ignore-missing-imports            # 0 issues
bandit -r src/domain -q                         # 0 issues required

# 2. Tests (REQUIRED)
pytest tests/unit tests/integration -q          # all passing

# 3. Coverage gates (REQUIRED)
pytest --cov=src/domain --cov-fail-under=100   # domain: 100%
pytest --cov=src/application --cov-fail-under=80  # application: ≥80%

# 4. DB tests (optional local, required in CI)
export RUN_DB_TESTS=1 DATABASE_URL_TEST=postgresql://...
pytest tests/unit tests/integration -q          # 3064+ tests
```

## Ejemplos de "Done"

### Caso 1: Nuevo use case
- ✅ Tests unit para DTO + execute()
- ✅ Tests integration con repo in-memory
- ✅ Tests E2E con Flask client (si aplica)
- ✅ Cobertura domain 100% (gate), application ≥80% (gate)
- ✅ **ruff clean** (0 errors)
- ✅ **black compliant** (all files)
- ✅ **mypy clean** (src/ + tests/, 0 issues)
- ✅ **bandit clean** (domain, 0 issues)
- ✅ CHANGELOG con entry

### Caso 2: Refactor facade (god-module split)
- ✅ Baseline tests pass (ej: 1972 actual)
- ✅ Nuevos tests unit para internos (ej: +44)
- ✅ Facade sigue <450 líneas
- ✅ Módulos internos 80%+ cobertura cada uno
- ✅ Backward compatible (firma pública sin cambios)
- ✅ Todas las quality gates passing (ruff, black, mypy, bandit)
- ✅ Total tests pass (3064+ con database habilitada)

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
