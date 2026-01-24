# Coverage Policy (100/80/0)

## Purpose
Forzar core robusto: domain sin excusas; application razonable; edges sin presión artificial.

## Targets
- domain: 100%
- application: >= 80%
- infrastructure/adapters: sin objetivo (pero tests cuando sea crítico)

## CI implementation
- Ejecutar coverage por paquete/capa (separado):
  - `--cov=src/domain --cov-fail-under=100`
  - `--cov=src/application --cov-fail-under=80`

## Exceptions (permitidas)
- Scripts/migrations generadas: documentar si se excluyen.

## How to verify
- CI en verde
- `make test` local
