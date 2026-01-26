# Import Policy

Permitido:
- domain -> (nadie)
- application -> domain
- infrastructure -> domain, application (solo para ports/use cases)
- adapters -> application, infrastructure (para build_services), domain (solo tipos si es inevitable)

Prohibido:
- domain importando application/infra/adapters
- application importando infrastructure/adapters
- infrastructure importando adapters

Regla adicional:
- Prohibido `src.` en imports. Usa imports absolutos del paquete.
- Evita imports circulares: si ocurre, extrae types a módulo estable o usa typing.TYPE_CHECKING.
