# Prompting Rules

## Purpose
Reducir alucinaciones y mantener el trabajo incremental, defendible y verificable (TDD + verify).

## Output discipline (regla clave)
- Si pido TEST → entrega SOLO tests.
- Si pido IMPLEMENTACIÓN → entrega SOLO implementación mínima para pasar tests.
- Si pido REFACTOR → entrega SOLO refactor (sin cambios funcionales).
- Si falta info para decidir → pregunta (máx. 3).

## TDD loop
1) RED: escribe un test que falle por el motivo correcto.
2) GREEN: implementa lo mínimo para pasar.
3) REFACTOR: elimina smells (duplicación, magia, complejidad, nombres).

## Prompt templates (copiable)
### RED (tests)
- “Escribe tests unitarios para X. Deben fallar inicialmente. No escribas implementación.”

### GREEN (mínimo)
- “Implementa lo mínimo para pasar los tests existentes. No añadas features.”

### REFACTOR
- “Refactoriza para eliminar duplicación y mejorar nombres sin cambiar comportamiento. Mantén tests verdes.”

## Retomar sesión
Incluye siempre:
- Estado actual (qué pasa / qué falla)
- Próximo objetivo (1 paso)
- Cómo verificar (`make lint && make test`)
