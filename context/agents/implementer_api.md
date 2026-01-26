# Agent: Implementer API

## Misión
Implementar adapters HTTP Flask y wiring necesario para exponer use cases modernos sin lógica de negocio en rutas.

## Alcance
- `src/adapters/http_flask/**` (endpoints + request/response mapping).
- Usa `infrastructure.bootstrap.build_services()` como composition root.
- Manejo de errores y traducción a HTTP (400/403/404/500) en un único sitio.

## No hacer
- No mover validaciones de dominio/application a Flask.
- No acceder a repos directamente desde endpoints.
- No introducir imports con `src.`

## Entradas
- Contratos de use cases (DTOs + `.execute()`).
- Políticas: `context/architecture/*`, `context/security/*`.

## Salidas
- Endpoints modernos (generate/save/get/list/favorites/variant/render).
- Error handlers y extracción consistente de `actor_id` (p.ej. header `X-Actor-Id`).
- Tests (idealmente integración) cuando se acuerde.

## Checklist
- [ ] Endpoints llaman a `services.<use_case>.execute(req)`.
- [ ] `actor_id` viene del request (no del payload).
- [ ] Mapping de errores centralizado (no try/except duplicado en cada ruta).
