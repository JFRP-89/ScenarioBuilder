# Security by Design (mínimos)

Principios:
- Deny-by-default
- Validación estricta de inputs
- Anti-IDOR (owner_id + visibility)
- Errores sin filtrar datos sensibles

Por capa:
- domain: invariantes + ValidationError
- application: valida actor_id/card_id, aplica authz helpers
- adapters: parse/validate JSON, extraer actor_id, mapear errores a HTTP

Regla: si no puedes justificar un acceso, se deniega.
