# Docker policy

Objetivo: entorno reproducible.

- `docker compose up` levanta:
  - API (Flask)
  - UI (Gradio) consumiendo la API
  - DB (Postgres) cuando aplique

Reglas:
- Variables vía env (`.env`)
- Volúmenes solo si facilitan desarrollo
- No meter secretos en imágenes
