# Testing Strategy 60/30/10

- 60% Unit:
  - domain (validaciones, invariantes)
  - application (use cases con fakes/in-memory)

- 30% Integration:
  - infrastructure (repos/generators/bootstrap)
  - wiring (smoke test: build_services + flujo mínimo)

- 10% E2E:
  - Flask endpoints (client)
  - Gradio smoke (opcional) consumiendo API real

Regla: no hagas E2E antes de tener estable application+infra.
