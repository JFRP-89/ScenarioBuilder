# AGENTS.md — ScenarioBuilder

Este archivo es **solo un índice y reglas globales mínimas**.  
El conocimiento detallado vive en `context/`.

## Estado actual (resumen)
- **Verificado**: 3064+ tests passing (1972 unit + 1000+ integration + 100+ e2e), branch `ui/alpha.0.10`
- **Quality gates**: ruff ✅, black ✅, mypy strict (205 src/ + 160 test/ files) ✅, bandit SAST ✅
- **Cobertura**: Domain **100%** (732 statements), Application **99%** (810 statements, exceeds 80% threshold)
- **Arquitectura por capas**: `domain/` (reglas), `application/` (use cases + ports), `infrastructure/` (implementaciones + bootstrap), `adapters/` (Flask/Gradio)
- **Use cases modernos**: application/ tiene DTOs + `.execute()`, sin lógica en adapters
- **Composition root**: `infrastructure.bootstrap.build_services()` construye todo el wiring
- **Patrón facade anti-god-module**: 15 facades (`wire_*.py`, ~250-450 líneas cada uno) con 4 paquetes internos:
  - `wiring/_detail/` (2 módulos: _render, _converters) — 45 tests
  - `wiring/_deployment/` (4 módulos: _form_state, _geometry, _ui_updates, _zone_builder) — 83 tests
  - `wiring/_scenography/` (4 módulos: _form_state, _polygon, _ui_updates, _builder) — 71 tests
  - `wiring/_generate/` (4 módulos: _preview, _create_logic, _resets, _outputs) — 44 tests
  - Total: 14 módulos internos, 243 wiring tests
- **Auth demo**: `adapters/ui_gradio/auth/` — login/logout/profile con PBKDF2, lockout (3 fails → 1h), validación allowlist, session management
- **Testing**: 60/30/10 strategy verificado — 1972 unit, 1000+ integration, 100+ e2e — cobertura domain 100%, application 99%

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
- `context/architecture/facade-pattern.md` — Patrón facade + módulos internos
- `context/architecture/ui-wiring-structure.md` — Estructura de wiring/ en Gradio

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
- `context/security/auth-demo.md` — Login/logout/profile, lockout, validación allowlist

### DevOps / Release
- `context/devops/ci-cd-policy.md`
- `context/devops/docker-policy.md`
- `context/release/changelog-policy.md`
