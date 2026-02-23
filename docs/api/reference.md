# API REST Reference

## Visión general

La API REST de Scenario Builder está implementada con **Flask** usando blueprints
modulares. Todos los endpoints requieren autenticación excepto `/health`.

**Base URL**: `http://localhost:8000` (Docker) / `http://localhost:5000` (dev)

**Content-Type**: `application/json` (excepto `/map.svg` que retorna `image/svg+xml`)

---

## Autenticación

### Headers requeridos

| Header | Descripción | Requerido en |
|--------|-------------|-------------|
| `X-Actor-Id` | Username del usuario actual | Todos los endpoints autenticados |
| `X-Session-Id` | ID de sesión activa | Endpoints con sesión |
| `X-CSRF-Token` | Token CSRF de la sesión | POST, PUT, DELETE |

---

## Endpoints

### Auth (`/auth`)

#### POST /auth/register

Registra un nuevo usuario.

**Request:**
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "SecureP@ss1",
  "full_name": "Alice Smith"
}
```

**Validaciones:**
- `username`: 3–32 chars, `^[a-z0-9][a-z0-9_-]*$`
- `email`: formato válido, único en el sistema
- `password`: 8+ chars, 1 mayúscula, 1 número, 1 carácter especial
- `full_name`: alfanumérico + espacios

**Response 201:**
```json
{
  "ok": true,
  "actor_id": "alice",
  "session_id": "abc123...",
  "csrf_token": "xyz789..."
}
```

**Response 400:**
```json
{
  "ok": false,
  "errors": ["username already taken"]
}
```

---

#### POST /auth/login

Inicia sesión. Lockout tras 3 intentos fallidos (1 hora).

**Request:**
```json
{
  "username": "alice",
  "password": "SecureP@ss1"
}
```

**Response 200:**
```json
{
  "ok": true,
  "session_id": "abc123...",
  "csrf_token": "xyz789..."
}
```

**Response 401:**
```json
{
  "ok": false,
  "errors": ["Invalid credentials"]
}
```

> Los mensajes son genéricos (anti-enumeración): no distingue "usuario no existe"
> de "contraseña incorrecta".

---

#### POST /auth/logout

Invalida la sesión actual.

**Headers requeridos:** `X-Session-Id`

**Response 200:**
```json
{
  "ok": true
}
```

---

#### GET /auth/me

Retorna el perfil del usuario autenticado.

**Headers requeridos:** `X-Session-Id`, `X-Actor-Id`

**Response 200:**
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

#### POST /auth/profile

Actualiza el perfil del usuario.

**Headers requeridos:** `X-Session-Id`, `X-Actor-Id`, `X-CSRF-Token`

**Request (campos opcionales):**
```json
{
  "full_name": "Alice Johnson",
  "email": "alice.new@example.com",
  "new_password": "NewP@ss123",
  "confirm_new_password": "NewP@ss123"
}
```

**Response 200:**
```json
{
  "ok": true
}
```

---

#### POST /auth/reauth

Re-autenticación para operaciones sensibles.

**Headers requeridos:** `X-Session-Id`

**Request:**
```json
{
  "password": "SecureP@ss1"
}
```

**Response 200:**
```json
{
  "ok": true,
  "session_id": "new_session_id..."
}
```

> El `session_id` se rota en re-auth por seguridad.

---

#### GET /auth/check-username

Verifica disponibilidad de username.

**Query params:** `username=alice`

**Response 200:**
```json
{
  "available": true
}
```

---

### Cards (`/cards`)

#### POST /cards

Crea un nuevo escenario.

**Headers requeridos:** `X-Actor-Id`, `X-CSRF-Token`

**Request:**
```json
{
  "seed": 42,
  "table_width_cm": 120,
  "table_depth_cm": 120,
  "game_mode": "matched",
  "constraints": [],
  "visibility": "private"
}
```

**Response 201:**
```json
{
  "card_id": "uuid-here",
  "seed": 42,
  "map_url": "/cards/uuid-here/map.svg"
}
```

---

#### GET /cards

Lista escenarios con filtro.

**Headers requeridos:** `X-Actor-Id`

**Query params:**
- `filter=mine` — solo cards del usuario
- `filter=public` — cards públicas
- `filter=shared_with_me` — cards compartidas con el usuario

**Response 200:**
```json
{
  "cards": [
    {
      "card_id": "uuid-1",
      "seed": 42,
      "mode": "matched",
      "owner_id": "alice",
      "visibility": "public",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

#### GET /cards/:card_id

Obtiene detalle completo de un escenario.

**Headers requeridos:** `X-Actor-Id`

**Response 200:**
```json
{
  "card_id": "uuid-1",
  "seed": 42,
  "mode": "matched",
  "owner_id": "alice",
  "visibility": "public",
  "table": {
    "width_cm": 120,
    "height_cm": 120,
    "preset": "standard"
  },
  "map_spec": { ... },
  "deployment": "...",
  "objectives": { ... },
  "constraints": [ ... ],
  "special_rules": [ ... ],
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Response 403:** Acceso denegado (anti-IDOR).

**Response 404:** Card no existe.

---

#### PUT /cards/:card_id

Actualiza un escenario. Solo el owner puede actualizar.

**Headers requeridos:** `X-Actor-Id`, `X-CSRF-Token`

**Request (campos opcionales):**
```json
{
  "visibility": "shared",
  "shared_with": ["bob", "charlie"],
  "constraints": ["constraint-1"]
}
```

**Response 200:**
```json
{
  "card_id": "uuid-1",
  "updated": true
}
```

---

#### DELETE /cards/:card_id

Elimina un escenario. Solo el owner puede eliminar.
Al eliminar, se limplan todos los favoritos asociados.

**Headers requeridos:** `X-Actor-Id`, `X-CSRF-Token`

**Response 200:**
```json
{
  "card_id": "uuid-1",
  "deleted": true
}
```

---

#### GET /cards/:card_id/map.svg

Descarga el mapa SVG del escenario.

**Headers requeridos:** `X-Actor-Id`

**Query params:**
- `display_units=cm` (default) | `in` | `ft`

**Response 200:**
```http
Content-Type: image/svg+xml

<svg viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
  <!-- 7 capas: bg, grid, zones, terrain, markers, labels, frame -->
</svg>
```

---

### Favorites (`/favorites`)

#### POST /favorites/:card_id/toggle

Añade o quita un escenario de favoritos. Requiere acceso de lectura al escenario.

**Headers requeridos:** `X-Actor-Id`, `X-CSRF-Token`

**Response 200:**
```json
{
  "card_id": "uuid-1",
  "is_favorite": true
}
```

---

#### GET /favorites

Lista los escenarios favoritos del usuario.

**Headers requeridos:** `X-Actor-Id`

**Response 200:**
```json
{
  "favorites": ["uuid-1", "uuid-2", "uuid-3"]
}
```

---

### Presets (`/presets`)

#### GET /presets

Lista los presets de mesa disponibles.

**Response 200:**
```json
[
  {"id": "standard", "width": 120, "height": 120},
  {"id": "massive", "width": 180, "height": 120}
]
```

---

### Health (`/health`)

#### GET /health

Health check. No requiere autenticación.

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## Códigos de error

| Código | Significado | Cuándo |
|--------|------------|--------|
| `200` | OK | Operación exitosa |
| `201` | Created | Recurso creado (cards, register) |
| `400` | Bad Request | Validación fallida (seed, mode, table) |
| `401` | Unauthorized | Sesión inválida o expirada |
| `403` | Forbidden | Sin permisos (anti-IDOR) |
| `404` | Not Found | Recurso no existe |
| `500` | Internal Server Error | Error inesperado del servidor |

### Formato de error

```json
{
  "error": "Descripción del error"
}
```

Los mensajes de error son descriptivos pero **no revelan datos internos**
(IDs de BD, stack traces, rutas de archivos del servidor).
