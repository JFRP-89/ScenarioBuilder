# Centaur Workflow (obligatorio)

Antes de escribir o modificar código, responde (máx. 3):
1) ¿Para qué lo quiero ahora? (bootstrap / feature / test / refactor / infra / adapters)
2) ¿Qué quiero entender? (arquitectura / seguridad / tests / SVG / CI / versionado)
3) ¿Dónde encaja? (domain / application / infrastructure / adapters / docs / context)

Si el contexto es claro:
- Declara supuestos en 1–3 bullets.
- Aplica el mínimo cambio necesario.

Regla operativa:
- Si se pide **RED**, SOLO tests (no tocar `src/`).
- Si se pide **GREEN**, implementación mínima para pasar tests.
- **REFACTOR** solo después de verde y sin cambiar comportamiento.
