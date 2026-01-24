# AuthZ & Anti-IDOR

## Purpose
Evitar Broken Access Control (IDOR): nadie accede a recursos privados que no son suyos.

## Core rule
Toda operación sobre un recurso debe validar:
- owner_id == current_user_id, o
- visibility == public (solo para lectura)

## Requirements
- Todo recurso persistible tiene `owner_id`.
- En MVP: CurrentUserProvider devuelve DEMO_USER_ID, pero el contrato queda listo para login real.

## Tests (mínimos obligatorios)
- private + otro user -> 403
- private + owner -> 200
- public + cualquiera -> 200
- write/delete siempre solo owner -> 403 si no owner

## How to verify
- integration tests en endpoints
- revisar que repos/queries filtran por owner_id/visibility
