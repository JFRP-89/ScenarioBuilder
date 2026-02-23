# Autenticación y Autorización

## Visión general

Scenario Builder implementa **autenticación completa** con sesiones y
**autorización deny-by-default** a nivel de dominio.

---

## Autenticación

### Flujo de registro

```
1. POST /auth/register {username, email, password, full_name}
2. Validar allowlist: username ^[a-z0-9][a-z0-9_-]{2,31}$
3. Validar email formato y unicidad
4. Validar password policy (8+ chars, mayúscula, número, especial)
5. Hash password con PBKDF2-HMAC-SHA256 (600K iter, salt 16 bytes)
6. Crear UserModel en BD
7. Auto-crear sesión
8. Retornar {session_id, csrf_token, actor_id}
```

### Flujo de login

```
1. POST /auth/login {username, password}
2. Validar allowlist de inputs
3. Verificar lockout: ≥3 fallos consecutivos → bloqueado 1 hora
4. Verificar credenciales (PBKDF2 constant-time compare)
5. Si falla: incrementar contador de fallos, mensaje genérico
6. Si ok: resetear contador, crear sesión
7. Retornar {session_id, csrf_token}
```

### Password hashing

```python
# PBKDF2-HMAC-SHA256
salt = os.urandom(16)     # 16 bytes únicos por usuario
iterations = 600_000       # NIST SP 800-132 recomendación
key_length = 32            # 256 bits
hash = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, key_length)
```

### Lockout

| Parámetro | Valor |
|-----------|-------|
| Intentos máximos | 3 consecutivos |
| Duración bloqueo | 1 hora |
| Reseteo | Login exitoso resetea el contador |
| Mensaje | Genérico (anti-enumeración) |

### Sesiones

| Campo | Descripción |
|-------|-------------|
| `session_id` | 64 caracteres, generado con `secrets` |
| `csrf_token` | Token CSRF vinculado a la sesión |
| `expires_at` | TTL configurable |
| `revoked_at` | Soft-revocation (logout) |
| `reauth_at` | Timestamp de última re-autenticación |

### Re-autenticación

Para operaciones sensibles (cambio de password), se requiere re-auth:

```
1. POST /auth/reauth {password}
2. Verificar password actual
3. Marcar reauth_at en la sesión
4. Rotar session_id (nuevo token)
```

---

## Autorización (AuthZ)

### Modelo

**Deny-by-default**: toda ruta no cubierta explícitamente retorna `False`.

```python
# domain/security/authz.py
def can_read(*, owner_id, visibility, current_user_id, shared_with) -> bool:
    if current_user_id == owner_id:
        return True
    if visibility == Visibility.PUBLIC:
        return True
    if visibility == Visibility.SHARED:
        return current_user_id in shared_with
    return False  # PRIVATE → solo owner

def can_write(*, owner_id, current_user_id) -> bool:
    return current_user_id == owner_id
```

### Anti-IDOR

Prevención de Insecure Direct Object Reference en todos los use cases:

1. **`actor_id` siempre del header**, nunca del payload.
2. **Verificación antes de retornar datos**: `card.can_user_read(actor_id)`.
3. **Verificación antes de mutar**: `card.can_user_write(actor_id)`.
4. **Respuesta uniforme**: 403 para acceso denegado (no 404, para no filtrar existencia).

### Permisos por operación

| Operación | Quién puede |
|-----------|-------------|
| `GetCard` | Owner, shared_with (si SHARED), todos (si PUBLIC) |
| `SaveCard` (update) | Solo owner |
| `DeleteCard` | Solo owner |
| `CreateVariant` | Solo owner de la card base |
| `ToggleFavorite` | Cualquiera con acceso de lectura |
| `ListCards` | Filtrado: mine=owner, public=todos, shared=allowlist |

---

## Headers de seguridad

| Header | Propósito | Requerido en |
|--------|----------|-------------|
| `X-Actor-Id` | Identificar usuario actual | Todos los endpoints autenticados |
| `X-Session-Id` | Validar sesión activa | Endpoints que requieren sesión |
| `X-CSRF-Token` | Prevenir CSRF | POST, PUT, DELETE |

---

## Validación de inputs (allowlist)

| Campo | Patrón | Límite |
|-------|--------|--------|
| `username` | `^[a-z0-9][a-z0-9_-]{2,31}$` | 3–32 chars |
| `password` | `^[A-Za-z0-9_-]{3,32}$` | 3–32 chars (allowlist) |
| `email` | RFC 5322 básico | Único |
| `display_name` | Alfanumérico + espacios | Opcional |

### Password policy (registro/cambio)

- Mínimo 8 caracteres
- Al menos 1 mayúscula
- Al menos 1 número
- Al menos 1 carácter especial
