# Documentación — Scenario Builder

Documentación técnica completa del proyecto.  
Para reglas de desarrollo y agentes, ver [`AGENTS.md`](../AGENTS.md) y [`context/`](../context/).

---

## Índice

### Producto

| Documento | Descripción |
|-----------|-------------|
| [Pitch](product/pitch.md) | Elevator pitch, problema, solución, diferenciación |
| [MVP Scope](product/mvp-scope.md) | Funcionalidades del MVP, criterios de aceptación |
| [User Stories](product/user-stories.md) | 15 historias de usuario con criterios de aceptación |
| [Content Model](product/content-model.md) | Modelo de contenido MESBG (CardItem, JSON, pipeline) |

### Arquitectura

| Documento | Descripción |
|-----------|-------------|
| [Overview](architecture/overview.md) | Clean Architecture, 4 capas, flujo de datos, decisiones |
| [Domain Model](architecture/domain-model.md) | Card, TableSize, MapSpec, AuthZ, errores, seed |
| [Import Policy](architecture/import-policy.md) | Reglas de dependencias entre capas |
| [Error Model](architecture/error-model.md) | Jerarquía de errores, mapeo HTTP en adapters |
| [Facade Pattern](architecture/facade-pattern.md) | Patrón facade para wiring Gradio |
| [SVG Rendering](architecture/svg-rendering.md) | Pipeline de 7 capas, shapes, unidades |

### API

| Documento | Descripción |
|-----------|-------------|
| [REST Reference](api/reference.md) | Endpoints, headers, request/response, códigos de error |

### Base de datos

| Documento | Descripción |
|-----------|-------------|
| [Schema](database/schema.md) | Modelos, tablas, diagrama ER, migraciones, dual backend |

### Seguridad

| Documento | Descripción |
|-----------|-------------|
| [Threat Model](security/threat-model.md) | STRIDE/OWASP, superficie de ataque, controles |
| [Authentication](security/authentication.md) | Login, registro, sesiones, lockout, PBKDF2, anti-IDOR |
| [SVG Hardening](security/svg-hardening.md) | Prevención XSS/XXE en SVG, defusedxml, allowlist |

### Testing

| Documento | Descripción |
|-----------|-------------|
| [Strategy](testing/strategy.md) | 60/30/10, cobertura verificada (domain 100%, application 80%), 3064+ tests |
| [Gradio Characterization Tests](testing/gradio-characterization-tests.md) | 121 tests de congelación de comportamiento |

### Design System

| Documento | Descripción |
|-----------|-------------|
| [Tactical Dark](design/design-system.md) | Tokens, componentes, tema Gradio, accesibilidad |

### Desarrollo

| Documento | Descripción |
|-----------|-------------|
| [Local Setup](development/local-setup.md) | Instalación, ejecución, debugging |
| [Contributing](development/contributing.md) | Workflow, DoD, convenciones, patterns |

### Deploy

| Documento | Descripción |
|-----------|-------------|
| [Runbook](deploy/runbook.md) | Docker Compose, variables, health checks, troubleshooting |

---

## Relación entre docs/ y context/

| Carpeta | Propósito | Audiencia |
|---------|----------|-----------|
| `docs/` | Documentación técnica del proyecto | Humanos + revisores |
| `context/` | Reglas operativas para agentes IA | Agentes IA (Copilot, etc.) |
| `AGENTS.md` | Índice y reglas globales mínimas | Ambos |

Los documentos en `context/` son prescriptivos ("haz esto"); los de `docs/` son
descriptivos ("así funciona").
