# TDD Policy

## Purpose
Asegurar calidad y diseño emergente: RED -> GREEN -> REFACTOR.

## Rules
- MUST FAIL: un test nuevo debe fallar antes de implementar.
- Implementación mínima: solo lo necesario para pasar.
- Refactor solo con tests verdes.
- Preferir tests en domain/application antes de tocar adapters.

## Anti-patterns
- Tests que dependen de tiempo real o random sin seed controlado.
- Tests gigantes end-to-end para lógica que podría ser unit.
- “Fix” sin test cuando hay lógica de negocio.

## How to verify
- `make test`
- Revisar que el PR incluye test(s) relevantes
