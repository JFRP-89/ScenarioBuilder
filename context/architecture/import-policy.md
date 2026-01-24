# Import Policy

## Purpose
Evitar dependencias cíclicas y “leaks” de infraestructura hacia el core.

## Allowed imports matrix
- domain: solo domain
- application: domain ✅
- infrastructure: domain ✅, application ✅
- adapters: domain ✅, application ✅, infrastructure ✅ (solo para wiring)

## Explicitly forbidden (ejemplos)
- domain -> flask/gradio/psycopg2/requests/os.environ/filesystem
- application -> flask/gradio/psycopg2 (usa puertos)
- adapters -> lógica de reglas (debe subir a domain/application)

## Enforcement
- Revisiones en PR
- Lint/import rules (si se añaden herramientas, documentarlas aquí)

## How to verify
- Buscar imports indebidos en PR
- Ejecutar `make lint && make test`
