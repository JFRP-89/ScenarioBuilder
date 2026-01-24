# Error Model

## Purpose
Errores consistentes y mapeables a API/UI sin filtrar detalles sensibles.

## Error types
- DomainError: violación de invariantes / validación.
- UseCaseError: orquestación (p.ej., recurso no encontrado, conflicto).
- AuthZError: acceso denegado (anti-IDOR).
- AdapterError: errores de parsing/mapping HTTP/UI (deben traducirse a respuestas limpias).

## Mapping (en adapters)
- DomainError -> HTTP 400 (error_code + message corto)
- AuthZError -> HTTP 403
- NotFound -> HTTP 404
- Unexpected -> HTTP 500 (sin stacktrace al usuario)

## Logging rules
- No loguear secretos, tokens, .env.
- No loguear payload completo si puede contener datos sensibles.
- Preferir logs estructurados con “request id” si existe.

## How to verify
- Tests de validación (400) y authz (403) en integration
- `make lint && make test`
