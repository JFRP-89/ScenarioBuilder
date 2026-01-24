# Security by Design

## Purpose
Aplicar seguridad desde el inicio: inputs estrictos, mínimos privilegios, y evidencias (tests).

## Attack surfaces (este proyecto)
- API Flask (payloads)
- JSON editable en `content/`
- Renderer SVG (inyección si no se escapan valores)
- Persistencia (cuando se active DB)

## Default controls
- Validación estricta (allowlist + tipos + límites)
- AuthZ por recurso (owner_id + visibility)
- Secrets fuera del repo (`.env` local + `.env.example`)
- Errores limpios (no stacktrace al usuario)

## Evidence
- Cada control del threat model debe tener test/evidencia verificable.

## How to verify
- Integration tests para 400/403
- Revisar `docs/security/threat-model.md`
