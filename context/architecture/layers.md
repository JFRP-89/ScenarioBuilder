# Architecture Layers

## Purpose
Mantener un monolito modular limpio: cambios fáciles, tests rápidos, y adapters “thin”.

## Layers
### src/domain/
- Responsabilidad: reglas puras, validación, modelos, invariantes.
- Prohibido: Flask, Gradio, DB, IO, HTTP.
- Verify: unit tests (coverage 100%).

### src/application/
- Responsabilidad: casos de uso + puertos; orquesta domain.
- Prohibido: detalles técnicos concretos (psycopg2, flask, filesystem direct).
- Verify: unit tests (coverage >=80).

### src/infrastructure/
- Responsabilidad: detalles (repos DB, content provider, SVG renderer, config).
- Prohibido: lógica de negocio (reglas) fuera de domain/application.
- Verify: integration tests cuando aplique.

### src/adapters/
- Responsabilidad: HTTP/UI mapping (Flask/Gradio).
- Regla de oro: NO lógica de negocio aquí.
- Verify: integration/e2e (según feature).

## How to verify
- Revisar imports (ver import-policy)
- Tests + coverage gates en CI
