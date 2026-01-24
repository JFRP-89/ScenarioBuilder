# CI/CD Policy

## Purpose
Gates automáticos: si falla lint/tests/coverage, no se mergea.

## CI must run on
- Pull requests
- Push a main

## Gates
- Lint: ruff + black --check
- Unit tests: domain 100% coverage, application >=80%
- Integration tests: cuando existan (mínimo smoke)

## Local workflow
- Ejecutar `make lint && make test` antes de abrir PR.

## How to verify
- GitHub Actions en verde
- Coverage gates cumplidos
