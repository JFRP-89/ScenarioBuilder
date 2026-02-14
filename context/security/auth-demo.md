# Auth Demo — Login / Logout / Profile

## Ubicación

```
src/adapters/ui_gradio/auth/
├── __init__.py        # API pública
├── _validators.py     # Validación allowlist (regex)
├── _store.py          # In-memory store + PBKDF2 hashing
└── _service.py        # Orquestación: validación → lockout → credenciales
```

## Usuarios demo

| username   | password   | email                 |
|------------|------------|-----------------------|
| demo-user  | demo-user  | demo@example.com      |
| alice      | alice      | alice@example.com     |
| bob        | bob        | bob@example.com       |
| charlie    | charlie    | charlie@example.com   |
| dave       | dave       | dave@example.com      |

Contraseñas hasheadas con **PBKDF2-HMAC-SHA256** (100 000 iteraciones, salt 32 bytes).

## Validación (allowlist)

| Campo        | Regex                           | Longitud |
|--------------|---------------------------------|----------|
| username     | `^[a-z0-9][a-z0-9_-]{2,31}$`   | 3–32     |
| password     | `^[A-Za-z0-9_-]{3,32}$`        | 3–32     |
| email        | `^[^@\s]+@[^@\s]+\.[^@\s]+$`   | estándar |
| display_name | `^[\x20-\x7E]{1,64}\Z`         | 1–64     |

> Se usa `\Z` (no `$`) para evitar bypass con `\n` al final.

## Lockout (brute force)

- **Máx. intentos fallidos**: 3 consecutivos por username.
- **Duración del bloqueo**: 1 hora (`timedelta(hours=1)`).
- **Reset automático**: al expirar la duración, o al autenticarse con éxito.
- **Mensajes genéricos**: sin revelar si el usuario existe o no.

## Flujo en la UI

1. **Sin login**: se muestra la pantalla de login como puerta de entrada. No hay usuario por defecto; `actor_id` empieza vacío (`""`).
2. **Login**: el usuario introduce username/password → `authenticate()`. Si es correcto, se oculta el panel de login y se muestra la top bar + la página de inicio.
3. **Post-login**: top bar muestra `"Logged in as: {username}"`, botones Profile y Logout.
4. **Profile**: panel editable (display name, email) con validación allowlist.
5. **Logout**: resetea `actor_id_state` a `""`, oculta todo el contenido y muestra de nuevo la pantalla de login.

## Integración con wiring

Cada `wire_*` acepta `actor_id_state: gr.State | None = None`.  
Si se pasa, el estado se incluye en los inputs de Gradio y el `actor_id` se propaga a los callbacks.  
Si no se pasa (backward compat), se usa `get_default_actor_id()`.

## Tests

```
tests/unit/adapters/ui_gradio/auth/
├── test_validators.py   # 27 tests
├── test_store.py        # 32 tests
└── test_service.py      # 42 tests
```

Total: **101 tests** nuevos, todos parametrizados con `pytest.mark.parametrize`.
