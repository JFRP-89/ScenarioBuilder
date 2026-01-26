# Error model

Objetivo: errores consistentes y mapeables.

- domain:
  - `ValidationError` para inputs inválidos / invariantes rotas.

- application:
  - MVP: puede propagar `ValidationError`.
  - Roadmap: errores propios (`NotFound`, `Forbidden`, `Conflict`) para mapear HTTP.

- adapters (Flask):
  - ÚNICO sitio donde se traduce a HTTP:
    - ValidationError -> 400
    - NotFound (o "not found") -> 404
    - Forbidden -> 403
    - fallback -> 500

Regla: no inventar códigos HTTP dentro de domain/application.
