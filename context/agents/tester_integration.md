# Agent: Tester Integration

## Misión
Validar infra/wiring: repos, generators, renderer y bootstrap (composition root).
**Estado actual (Feb 2026)**: 1000+ integration tests pasando, con DB support habilitado

## Alcance
- `tests/integration/**` (infrastructure layer).
- Smoke tests de wiring: `build_services()` + flujo mínimo.
- Tests de bootstrap con mocks/stubs.
- Flask route integration tests con `test_client()`.
- 100+ tests con `@pytest.mark.db` para DB-dependent tests.

## Estrategia
- Un test por contrato clave (repo/generator/renderer).
- Evitar asserts frágiles (no estilos exactos, no strings demasiado rígidas).
- Tests marcados con `@pytest.mark.db` se ejecutan solo con `RUN_DB_TESTS=1`.
- Backup: in-memory repos si PostgreSQL no está disponible.

## Salidas
- Tests que fallen si se rompe el wiring o el comportamiento observable.
- Guía de comandos de verificación.

## Checklist
- [ ] `build_services()` crea instancias independientes por llamada.
- [ ] Repos in-memory aislados por instancia (cleanup entre tests).
- [ ] Renderer no revienta con input vacío.
- [ ] Flask routes retornan status codes correctos (200, 400, 403, 404).
- [ ] Error mapping: ValidationError → 400, ForbiddenError → 403.
- [ ] DB tests skip gracefully sin DATABASE_URL_TEST.
