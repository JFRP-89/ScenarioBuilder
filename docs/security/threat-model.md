# Threat Model — Scenario Builder

## Metodología

Análisis de amenazas basado en **STRIDE** (Microsoft) con controles mapeados a
**OWASP Top 10** y **CWE**.  
Mentalidad: **Security by Design** — deny-by-default en todas las capas.

---

## Superficie de ataque

```
┌──────────────────────────────────────────────┐
│               Internet (usuario)              │
├──────────────────────────────────────────────┤
│  Flask API (REST)        Gradio UI (WebSocket)│
│  /auth/* /cards/*        /sb/*                │
│  /favorites/* /health                         │
├──────────────────────────────────────────────┤
│  Application Layer (use cases + ports)        │
├──────────────────────────────────────────────┤
│  Infrastructure (PostgreSQL, file system)     │
└──────────────────────────────────────────────┘
```

---

## Matriz de amenazas

### A1 — Broken Access Control (OWASP #1)

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| IDOR en cards | Acceso a cards adivinando `card_id` | Alta |
| Escalación de privilegios | Editar/eliminar cards de otro usuario | Alta |
| Bypass de visibilidad | Leer cards PRIVATE de otros | Alta |

| Control | Implementación | Evidencia |
|---------|---------------|-----------|
| Deny-by-default | `can_read()` / `can_write()` siempre devuelven `False` en rutas desconocidas | `domain/security/authz.py` |
| Owner-only write | `can_write(owner_id, current_user_id)` — solo owner | `domain/security/authz.py` |
| Visibility check | PRIVATE=owner, SHARED=allowlist, PUBLIC=autenticados | Tests: `test_visibility_authz.py` |
| Actor validation | `actor_id` desde header, nunca desde payload | `adapters/http_flask/middleware.py` |

---

### A2 — Cryptographic Failures (OWASP #2)

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| Passwords en texto plano | Almacenar contraseñas sin hash | Crítica |
| Salt débil | Reutilizar salt entre usuarios | Alta |
| Hash rápido | Usar MD5/SHA1 para passwords | Alta |

| Control | Implementación | Evidencia |
|---------|---------------|-----------|
| PBKDF2-HMAC-SHA256 | 600K iteraciones (producción), 100K (demo) | `infrastructure/auth/user_store.py` |
| Salt único 16–32 bytes | `os.urandom()` por usuario | `infrastructure/auth/user_store.py` |
| Password policy | 8+ chars, mayúscula, número, carácter especial | `infrastructure/auth/validators.py` |

---

### A3 — Injection (OWASP #3)

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| SQL Injection | Queries construidas con string concatenation | Crítica |
| XSS via SVG | Inyección de JavaScript en SVG renderizado | Alta |
| XXE | Parsing de XML malicioso con DTD externo | Alta |
| Command Injection | Ejecución de comandos vía inputs | Crítica |

| Control | Implementación | Evidencia |
|---------|---------------|-----------|
| Queries parametrizadas | SQLAlchemy ORM con bind params | `infrastructure/repositories/*.py` |
| SVG sanitizer | Allowlist de tags + atributos, escape | `adapters/http_flask/svg_sanitizer.py` |
| defusedxml | DTD deshabilitados, sin entity expansion | Dependencia en `requirements.txt` |
| Input validation | Allowlist de caracteres en todas las entradas | `domain/validation.py`, `infrastructure/auth/validators.py` |

---

### A4 — Insecure Design (OWASP #4)

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| Lógica de negocio en adapters | Bypass de validaciones | Media |
| Business logic bypass | Saltar validaciones de dominio | Alta |

| Control | Implementación | Evidencia |
|---------|---------------|-----------|
| Clean Architecture | Validación en domain `__post_init__`, nunca en adapters | `domain/cards/card.py` |
| Frozen dataclasses | Imposible mutar después de creación | Todas las entidades |
| Import policy | Domain no importa de capas externas | `test_domain_imports.py` |

---

### A5 — Security Misconfiguration (OWASP #5)

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| Secretos en código | DATABASE_URL hardcoded | Crítica |
| Debug en producción | Stack traces expuestos | Alta |
| Puertos innecesarios | Servicios expuestos | Media |

| Control | Implementación | Evidencia |
|---------|---------------|-----------|
| `.env` excluido | `.gitignore` incluye `.env` | Repositorio |
| `.env.example` sanitizado | Solo placeholders, sin valores reales | `.env.example` |
| Docker non-root | `appuser` (UID 1000) | `Dockerfile` |
| Error sanitization | Mensajes genéricos, sin stack traces | `adapters/http_flask/error_contract.py` |

---

### A6 — Vulnerable Components (OWASP #6)

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| Dependencias con CVEs | Versiones desactualizadas | Variable |

| Control | Implementación | Evidencia |
|---------|---------------|-----------|
| SAST (Bandit) | Análisis estático de seguridad | `scripts/`, `reports/bandit_*.json` |
| Ruff rules | Reglas de seguridad (B, RUF) | `pyproject.toml` |
| Dependencias pinned | Versiones fijas en `requirements.txt` | `requirements.txt` |

---

### A7 — Authentication Failures (OWASP #7)

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| Brute force | Probar contraseñas por fuerza bruta | Alta |
| Session fixation | Reutilizar session IDs | Media |
| User enumeration | Distinguir "no existe" de "password incorrecto" | Media |

| Control | Implementación | Evidencia |
|---------|---------------|-----------|
| Lockout temporal | 3 fallos → 1 hora bloqueado | `infrastructure/auth/user_store.py` |
| Anti-enumeración | Mensaje genérico "Invalid credentials" | `infrastructure/auth/auth_service.py` |
| Session rotation | Nuevo session_id en re-auth | `infrastructure/auth/auth_service.py` |
| CSRF tokens | Requerido en POST/PUT/DELETE | `adapters/http_flask/middleware.py` |
| Session expiration | TTL con `expires_at` | `infrastructure/db/models.py` |

---

### A8 — Data Integrity Failures (OWASP #8)

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| Seed manipulation | Modificar seeds para obtener resultados favorables | Baja |
| Data tampering | Modificar cards de otros | Alta |

| Control | Implementación | Evidencia |
|---------|---------------|-----------|
| Deterministic seeds | SHA-256 derivation; seed → resultado fijo | `domain/seed.py` |
| Owner-only write | Write check en todos los use cases | Tests de autorización |
| Frozen models | Inmutabilidad previene tampering en memoria | Dataclasses frozen |

---

### Específicas de la aplicación

| Riesgo | Control | Test/Evidencia |
|--------|---------|----------------|
| Abuso de API (DDoS) | Rate limiting (futuro) | Documentado en roadmap |
| SSRF vía URLs | No se aceptan URLs de usuario | Input validation |
| Deserialización maliciosa | JSON schema validado | `domain/validation.py` |
| Persistencia insegura | Queries parametrizadas + ORM | Tests de repositorio |
| Datos sensibles en logs | Sanitización en error handlers | Error contract |

---

## Herramientas de seguridad

| Herramienta | Propósito | Comando |
|-------------|----------|---------|
| Bandit | SAST Python | `bandit -r src/ -f json` |
| Ruff (B rules) | Best practices + seguridad | `ruff check .` |
| defusedxml | Anti-XXE | Importado en SVG sanitizer |
| SonarQube | Code quality + security | Integración externa |

---

## Pendientes (roadmap de seguridad)

- [ ] Rate limiting en API (por IP / por usuario)
- [ ] Headers de seguridad HTTP (CSP, HSTS, X-Frame-Options)
- [ ] Audit log de acciones sensibles
- [ ] Pruebas de penetración (DAST)
- [ ] Rotación de credenciales automatizada
- [ ] Sanitización de logs (eliminar datos sensibles)
