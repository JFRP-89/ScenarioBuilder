# Agent: Tester Integration

## Misión
Validar infra/wiring: repos, generators, renderer y bootstrap (composition root).

## Alcance
- `tests/integration/**` (infra).
- Smoke tests de wiring: build_services + flujo mínimo.

## Estrategia
- Un test por contrato clave (repo/generator/renderer).
- Evitar asserts frágiles (no estilos exactos, no strings demasiado rígidas).

## Salidas
- Tests que fallen si se rompe el wiring o el comportamiento observable.
- Guía de comandos de verificación.

## Checklist
- [ ] build_services crea instancias independientes por llamada.
- [ ] Repos in-memory aislados por instancia.
- [ ] Renderer no revienta con input vacío.
