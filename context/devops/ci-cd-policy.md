# CI/CD Policy

Objetivo: PRs verificables y listas para merge.

**CI debe ejecutar** (en orden):

1. **Lint**: `ruff check src tests` → 0 errors requerido
2. **Format**: `black --check src tests` → compliant requerido
3. **Type check**: `mypy src --ignore-missing-imports` → 0 issues requerido
4. **Security**: `bandit -r src/domain -q` → 0 issues en domain requerido
5. **Tests**: `pytest -q tests/unit tests/integration` → all passing requerido
6. **Coverage gates**:
   - `pytest --cov=src/domain --cov-fail-under=100` → 100% obligatorio
   - `pytest --cov=src/application --cov-fail-under=80` → ≥80% obligatorio

**Reglas**:
- Nada se mergea con CI rojo (100% policy: si un gate falla, PR no entra).
- PR template exige:
  - [ ] Tests verdes (local + CI)
  - [ ] CHANGELOG actualizado (si cambio notable)
  - [ ] Checklist de seguridad mínimo (deny-by-default, anti-IDOR)
  - [ ] Cobertura gates: domain 100%, application ≥80%
- CI debe ejecutarse en cada push a feature branch.
- Main branch: require approval + CI green.
