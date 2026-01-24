# Changelog Policy (Keep a Changelog + SemVer)

## Purpose
Versionado profesional y cambios “para humanos”.

## Rules
- Seguir Keep a Changelog 1.1.0 (ES).
- Mantener sección `## [Unreleased]`.
- PR con cambio notable -> actualizar `Unreleased`.
- Categorías: Added, Changed, Deprecated, Removed, Fixed, Security.

## SemVer quick rules
- patch: bugfix compatible
- minor: nueva feature compatible
- major: breaking change

## PR expectations
- Template PR debe incluir:
  - tipo de cambio
  - impacto SemVer
  - checklist (tests, docs, changelog si aplica)

## How to verify
- `CHANGELOG.md` actualizado correctamente
- Tag/release cuando toque
