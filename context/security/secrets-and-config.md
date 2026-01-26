# Secrets and config

- Secretos fuera del repo: `.env` local + `.env.example` en repo.
- Nunca hardcodear:
  - DB URL, tokens, keys
- Infra lee config desde env (y aplica defaults seguros).

Reglas:
- `.env.example` documenta variables requeridas.
- `docker compose` usa env vars, no valores pegados en código.
