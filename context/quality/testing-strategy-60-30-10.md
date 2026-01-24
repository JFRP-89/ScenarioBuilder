# Testing Strategy (60/30/10)

## Purpose
Equilibrar velocidad (unit) con confianza (integration/e2e).

## Distribution
- 60% Unit: domain + application (rápidos, deterministas).
- 30% Integration: Flask test client, repos/providers reales o DB en contenedor.
- 10% E2E: UI (Gradio) + API levantada, flujos MVP.

## What goes where
- tests/unit/: validaciones, heurísticas, modelos, casos de uso sin IO.
- tests/integration/: endpoints, authz/IDOR, persistencia, validación de request/response.
- tests/e2e/: “Generate -> Preview -> Save -> List/Favorite” (flujos).

## How to verify
- `python -m pytest tests/unit`
- `python -m pytest tests/integration`
- `python -m pytest tests/e2e` (cuando exista)
