# Secrets & Config

## Purpose
Evitar filtrado de secretos y mantener configuración reproducible.

## Rules
- Nunca commitear `.env` real.
- Mantener `.env.example` como plantilla sin secretos.
- Variables típicas: ENV, LOG_LEVEL, DATABASE_URL / POSTGRES_*, etc.
- No imprimir env completa en logs.

## Docker/Compose
- Compose usa variables/`env_file` y valores demo si aplica.
- Para producción: secrets fuera del repo (documentar en runbook).

## How to verify
- `git grep` de tokens/keys (si se añade un check)
- revisión PR: no hay secretos en diff
