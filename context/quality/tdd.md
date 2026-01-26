# TDD (RED → GREEN → REFACTOR)

RED:
- Escribe tests que fallen.
- Alcance mínimo: no “arregles” producción en RED si no toca.
- Si se pide “solo tests”, NO tocar `src/`.

GREEN:
- Implementación mínima para pasar tests.
- Sin refactor grande.

REFACTOR:
- Solo con tests en verde.
- No cambia comportamiento ni contratos.
- Reduce duplicación, mejora nombres, elimina legacy cuando ya no se usa.

Regla práctica:
- Un PR ideal: RED+GREEN (y refactor pequeño si es seguro).
