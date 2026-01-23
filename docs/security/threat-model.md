# Threat Model

Tabla riesgo → control → test (mentalidad OWASP/MITRE).

| Riesgo | Control | Test/Evidencia |
|---|---|---|
| IDOR en cartas | owner_id + validación de acceso | tests/unit de ownership |
| Inyección en inputs | validación estricta | tests/unit de validación |
| Exposición de secretos | .env fuera del repo | revisión de config |
| Datos sensibles en logs | sanitización | tests de logger (TODO) |
| Abuso de API | rate limiting futuro | doc de mitigación |
| SSRF vía URLs | bloquear entradas externas | tests de validación |
| Deserialización maliciosa | JSON schema | tests de schema |
| Persistencia insegura | queries parametrizadas | tests de repo |
