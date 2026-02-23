# Coverage Policy 100/80/0

**Estado verificado (Feb 2026)**:
- domain: **100%** (732 statements) ✅
- application: **99%** (810 statements, exceeds 80% threshold) ✅
- infrastructure/adapters: sin objetivo (0 gate)

**Reglas**:
- No bajar coverage por mover tests/archivos.
- Si migra legacy → asegura equivalencia por tests antes de borrar.
- Domain 100% es **obligatorio** en toda PR.
- Application ≥80% es **obligatorio** en toda PR.

**Verificación**:
```bash
# Domain: must be 100%
pytest --cov=src/domain --cov-fail-under=100 tests/unit

# Application: must be ≥80%
pytest --cov=src/application --cov-fail-under=80 tests/unit

# Full suite with DB
export RUN_DB_TESTS=1 DATABASE_URL_TEST=postgresql://...
pytest tests/unit tests/integration -q
```
