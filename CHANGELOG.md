# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato esta basado en [Keep a Changelog 1.1.0](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [SemVer](https://semver.org/lang/es/).

## [Unreleased]
### Changed
- Preparacion de release branch `release/0.1.1`.

## [0.1.1] - 2026-02-23
### Changed
- Ajustes de estabilidad en UI Gradio (navegacion, listado, favoritos y componentes).
- Afinado de flujos de autenticacion y lectura de datos para escenarios.
- Mejora de pruebas unitarias/integracion y compatibilidad general de la release.

## [0.1.0] - 2026-02-23
### Added
- Arquitectura por capas consolidada (`domain`, `application`, `infrastructure`, `adapters`).
- Adapters Flask y Gradio con composition root via `infrastructure.bootstrap.build_services()`.
- Soporte de autenticacion demo (login/logout/profile), validacion allowlist y lockout.
- Persistencia in-memory y Postgres para escenarios, favoritos y sesiones.
- Generacion de escenarios con seed determinista, render SVG y controles de seguridad.
- Cobertura amplia de tests unitarios, integracion y e2e.

### Changed
- Endurecimiento de CI/CD y estandarizacion de pipelines de validacion.
- Refactor de wiring UI con facades y modulos internos para evitar god modules.
- Mejora de validaciones de entrada y controles de acceso (deny-by-default, anti-IDOR).

### Security
- Hardening de render/sanitizacion SVG.
- Reglas de acceso y ownership reforzadas en rutas API y UI.
