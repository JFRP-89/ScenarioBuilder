# Runbook de despliegue

## Objetivo
Despliegue reproducible con Docker Compose para API, UI y Postgres.

## Pasos
1) Copiar `.env.example` a `.env` y ajustar valores.
2) Ejecutar `docker compose up`.
3) Verificar salud en `/health`.

## Rollback
Parar servicios con `docker compose down` y volver a la versión anterior.
