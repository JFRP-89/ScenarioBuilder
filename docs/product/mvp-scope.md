# MVP Scope — Scenario Builder

## Definición del MVP

El Minimum Viable Product cubre el flujo completo de un jugador de MESBG:
**crear → visualizar → guardar → compartir** escenarios tácticos.

---

## Funcionalidades incluidas en el MVP

### 1. Generación de escenarios

| Feature | Detalle |
|---------|---------|
| Generación por seed | Seed numérico determinista (0–2³¹−1). Seed 0 = modo manual. |
| Tres modos de juego | `casual`, `narrative`, `matched` — cada uno selecciona contenido diferente. |
| Contenido MESBG | Layouts, deployments, objectives, twists, story hooks, constraints cargados desde JSON. |
| Scoring (matched) | Puntuación base 100, −10 por risk flag. Floor en 0. |
| Constraints | Validación de pares incompatibles. |
| Shapes deterministas | Escenografía generada con RNG seeded + SHA-256 para reintentos. |

### 2. Renderizado SVG

| Feature | Detalle |
|---------|---------|
| Mesa configurable | Standard (120×120 cm), Massive (180×120 cm), Custom (60–300 cm). |
| Unidades | Conversión cm / inches / feet con precisión de 2 decimales. |
| Capas SVG | 7 capas: background → grid → zones → terrain → markers → labels → frame. |
| Cotas (acotaciones) | Dimensiones exactas en bordes del mapa. |
| Brújula | Orientación cardinal (N/S/E/W). |
| Seguridad SVG | Hardening XSS/XXE con `defusedxml` + allowlist de tags. |

### 3. Persistencia

| Feature | Detalle |
|---------|---------|
| CRUD completo | Crear, leer, actualizar, eliminar cards. |
| Dual backend | In-memory (dev/test) o PostgreSQL (producción). Mismo contrato via ports. |
| Migraciones | Alembic con upgrade/downgrade versionados. |
| Modelos DB | `CardModel`, `UserModel`, `SessionModel`, `FavoritesModel`. |

### 4. Visibilidad y compartición

| Feature | Detalle |
|---------|---------|
| Private | Solo el owner puede ver/editar. |
| Shared | Owner + lista allowlist de usuarios. |
| Public | Visible para todos los autenticados. |
| Anti-IDOR | Deny-by-default; verificación de permisos antes de retornar datos. |

### 5. Sistema de favoritos

| Feature | Detalle |
|---------|---------|
| Toggle | `POST /favorites/<card_id>/toggle` — añade o quita. |
| Listado | `GET /favorites` — cards favoritas del usuario. |
| Limpieza | Al eliminar una card, se limpian todos los favoritos asociados. |

### 6. Autenticación y perfiles

| Feature | Detalle |
|---------|---------|
| Registro | Username único + email único. Password policy: 8+ chars, mayúscula, número, especial. |
| Login | Sesiones con CSRF token. Lockout: 3 intentos → 1 hora. |
| Perfil editable | Nombre, email, contraseña. Re-auth para operaciones sensibles. |
| Anti-enumeración | Mensajes de error genéricos ("Invalid credentials"). |

### 7. Galería

| Feature | Detalle |
|---------|---------|
| Listado filtrado | Mine / public / shared_with_me. |
| Vista de detalle | Todos los datos del escenario + preview SVG. |
| Clonación | Crear variante con nuevo seed manteniendo configuración base. |

### 8. Interfaces de usuario

| Feature | Detalle |
|---------|---------|
| API REST | Flask con blueprints (auth, cards, favorites, health, presets). |
| UI web | Gradio 4.x con formularios de creación/edición, galería, perfil, preview SVG. |
| App combinada | FastAPI envolviendo Flask (WSGI) + Gradio en mismo origen. |

---

## Fuera del MVP (roadmap)

| Feature | Prioridad | Release estimado |
|---------|-----------|-----------------|
| Export PDF/imagen | Alta | v0.2.0 |
| Wizard UX con presets de mesa | Alta | v0.2.0 |
| Creación de figuras | Media | v0.2.0 |
| Soporte multi-juego | Media | v0.3.0+ |
| Modo torneo (brackets) | Baja | v0.3.0+ |
| Rate limiting API | Media | v0.2.0 |
| CI/CD con GitHub Actions | Alta | v0.2.0 |
| Notifications (WebSocket) | Baja | v0.3.0+ |

---

## Criterios de aceptación del MVP

1. ✅ Un usuario puede registrarse, loguearse y editar su perfil.
2. ✅ Un usuario puede generar un escenario con seed reproducible.
3. ✅ El mapa SVG muestra mesa con cotas, brújula, deployment zones y escenografía.
4. ✅ Las cards se persisten y se pueden listar/filtrar.
5. ✅ El owner controla la visibilidad (private/shared/public).
6. ✅ Los favoritos funcionan como toggle con cleanup automático.
7. ✅ El sistema rechaza accesos no autorizados (anti-IDOR).
8. ✅ **3064+ tests** pasan (1972 unit, 1000+ integration, 100+ e2e) con BD enabled.
9. ✅ **Quality gates**: ruff 0 errors, black compliant, mypy 0 issues, bandit clean.
10. ✅ Deploy funcional con `docker compose up`.
11. ✅ Domain 100% cobertura verificada, Application 99% (exceeds 80% target).
