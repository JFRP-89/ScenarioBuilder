# Centaur Workflow

## Purpose
Asegurar que cada cambio tiene intención clara, encaja en la arquitectura y es verificable (tests + gates) antes de escribir código.

## Checklist (antes de tocar código)
1) ¿Para qué quieres esto ahora? (bootstrap / skeleton / feature / test / refactor / infra / docs)
2) ¿Qué quieres entender tú? (arquitectura / seguridad / tests / SVG / CI / versionado)
3) ¿Dónde encaja? (domain / application / infrastructure / adapters)
4) ¿Cuál es el test RED mínimo que lo demuestra? (o evidencia equivalente si es docs/infra)
5) ¿Qué superficie atacable toca? (API payload / JSON content / SVG / authz)
6) ¿Cómo verifico al final? (`make lint && make test` y si aplica smoke `/health`)

## Stop conditions
- Si falta información clave → pregunta antes (máx. 3 preguntas).
- Si `verify` falla → no continúes con más cambios; arregla primero.

## How to verify
- `make lint && make test`
- (si hay cambios de runtime) `docker compose up` y comprobar `/health`
