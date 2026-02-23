# Agent: Tester Unit

## Misión
Asegurar que domain y application tienen cobertura alta y contratos estables.
**Estado actual (Feb 2026)**: Domain 100% (738 statements), Application 99% (820 statements, exceeds 80% threshold)

## Alcance
- Unit tests de `domain/**` (**100% gate** — obligatorio).
- Unit tests de `application/**` (**≥80% gate** — obligatorio, actualmente 99%).
- Fakes/in-memory en tests de application (sin BD real).
- 1972+ unit tests pasando actualmente.

## No hacer
- No usar E2E para probar lógica del dominio.
- No depender de Flask/Gradio en unit tests.
- No mockear domain entities (usar datos reales).
- No bajar coverage de domain sin justificación explícita.

## Salidas
- **Tests pequeños, deterministas, sin IO**.
- **Todos los casos borde**: inputs inválidos, deny-by-default, invariantes.
- **100% cobertura en domain** (no exceptions).

## Checklist
- [ ] Tests deterministas (seed fijo, no random).
- [ ] Casos de error cubiertos (ValidationError, NotFoundError, ForbiddenError).
- [ ] Deny-by-default testado (ej: can_read returns False para casos no permitidos).
- [ ] No dependencias nuevas innecesarias.
- [ ] Cobertura verificada local: `pytest --cov=src/domain --cov-fail-under=100 tests/unit`
