# Agent: Tester Unit

## Misión
Asegurar que domain y application tienen cobertura alta y contratos estables.

## Alcance
- Unit tests de `domain/**` (100% gate).
- Unit tests de `application/**` (>=80% gate).
- Fakes/in-memory en tests de application (sin DB real).

## No hacer
- No usar E2E para probar lógica del dominio.
- No depender de Flask/Gradio en unit.

## Salidas
- Tests pequeños, deterministas, sin IO.
- Casos borde: inputs inválidos, deny-by-default, invariantes.

## Checklist
- [ ] Tests deterministas (seed fijo).
- [ ] Casos de error cubiertos (ValidationError).
- [ ] No dependencias nuevas innecesarias.
