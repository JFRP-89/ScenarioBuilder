# CI/CD Policy

Objetivo: PRs verificables.

CI debe ejecutar:
- Lint: `ruff check`
- Tests: `pytest -q`
- Coverage gates (domain 100%, application >=80%) si están configurados

Reglas:
- Nada se mergea con CI rojo.
- PR template exige:
  - tests verdes
  - changelog si aplica
  - security checklist mínimo
