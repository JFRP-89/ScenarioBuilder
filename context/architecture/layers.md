# Capas (monolito modular)

## domain/
- Reglas puras, validación, invariantes, modelos.
- Sin IO, sin repos, sin frameworks.

## application/
- Casos de uso (DTO + `.execute()`), orquestación.
- Define **ports** (interfaces) que necesita.
- No contiene detalles de persistencia ni UI/HTTP.

## infrastructure/
- Implementa ports: repos, generators, renderers.
- Contiene `bootstrap` / `build_services()` (composition root).

## adapters/
- Flask: endpoints HTTP, parseo/mapeo, error mapping.
- Gradio: UI; idealmente consume la API Flask.
- Sin lógica de negocio: llama a application via services.

Regla: el wiring vive en infra; los adapters solo “consumen” wiring.
