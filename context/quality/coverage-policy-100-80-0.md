# Coverage Policy 100/80/0

- domain: 100%
- application: >= 80%
- infrastructure/adapters: sin objetivo (0 gate)

Reglas:
- No bajar coverage por mover tests/archivos.
- Si migra legacy -> asegura equivalencia por tests antes de borrar.

Verificación típica:
- `pytest --cov=src/domain --cov-fail-under=100 ...`
- `pytest --cov=src/application --cov-fail-under=80 ...`
