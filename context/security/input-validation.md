# Input Validation

## Purpose
Rechazar inputs maliciosos/incorrectos por defecto (Security by Design).

## Validation strategy
- Adapter layer: valida request/params (schema) antes de ejecutar use case.
- Domain layer: valida invariantes (modelos y reglas).
- Rechazo por defecto: no aceptar campos extra sin intención.

## Limits (ejemplos de política)
- Tamaños de mesa con rangos razonables.
- map_spec: límites de shapes/puntos y bounds.
- Strings: longitudes máximas y allowlist si aplica.

## Error handling
- 400 con mensaje corto + error_code (sin filtrar detalles internos).

## How to verify
- tests unit (domain invariantes)
- tests integration (payload inválido -> 400)
