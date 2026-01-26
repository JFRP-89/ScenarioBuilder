# AGENTS.md — ScenarioBuilder

Este archivo es **solo un índice y reglas globales mínimas**.  
El conocimiento detallado vive en `context/`.

## Estado actual (resumen)
- Arquitectura por capas: `domain/` (reglas), `application/` (use cases + ports), `infrastructure/` (implementaciones + bootstrap), `adapters/` (Flask/Gradio).
- `application/` ya tiene use cases modernos (DTO + `.execute()`).
- `infrastructure/` ya tiene: repos in-memory (cards/favorites), generators (id/seed), scenario generator, SVG renderer y `build_services()` (composition root).
- Siguiente fase: migrar adapters (Flask/Gradio) a `build_services()` y endpoints modernos.

## Reglas globales (mínimas)
1) **Nada de lógica de negocio en adapters** (Flask/Gradio solo HTTP/UI + mapeos).  
2) `domain/` no importa de ninguna otra capa.  
3) `application/` importa `domain/` y define **ports**; no importa `infrastructure/` ni `adapters/`.  
4) `infrastructure/` implementa ports y construye wiring (`build_services()`); no importa `adapters/`.  
5) Prohibido `src.` en imports (usa imports absolutos desde el paquete).  
6) TDD: **RED → GREEN → REFACTOR** (ver `context/quality/tdd.md`).  
7) Security by design: deny-by-default + anti-IDOR (ver `context/security/authz-anti-idor.md`).  
8) Errores: `ValidationError` en dominio; HTTP mapping solo en adapters (ver `context/architecture/error-model.md`).
9) **Composition root**: los adapters (Flask/Gradio) deben construir servicios **solo** vía `infrastructure.bootstrap.build_services()` (no instanciar repos/use cases a mano).  
10) Si el prompt dice **RED**: **solo tests** (no tocar `src/`).

## Comandos rápidos
- Tests: `pytest -q`
- Lint: `ruff check .`

## Índice de contexto

### Workflow
- `context/workflow/centaur.md`
- `context/workflow/prompting.md`

### Agentes
- `context/agents/planner.md`
- `context/agents/implementer_api.md`
- `context/agents/implementer_ui.md`
- `context/agents/refactorer.md`
- `context/agents/release_manager.md`
- `context/agents/security_reviewer.md`
- `context/agents/tester_unit.md`
- `context/agents/tester_integration.md`
- `context/agents/tester_e2e.md`

### Arquitectura
- `context/architecture/layers.md`
- `context/architecture/import-policy.md`
- `context/architecture/error-model.md`

### Calidad
- `context/quality/tdd.md`
- `context/quality/testing-strategy-60-30-10.md`
- `context/quality/coverage-policy-100-80-0.md`
- `context/quality/definition-of-done.md`
- `context/quality/solid-checklist.md`

### Seguridad
- `context/security/security-by-design.md`
- `context/security/authz-anti-idor.md`
- `context/security/input-validation.md`
- `context/security/secrets-and-config.md`

### DevOps / Release
- `context/devops/ci-cd-policy.md`
- `context/devops/docker-policy.md`
- `context/release/changelog-policy.md`
