# Esquema de Base de Datos

## Motor

**PostgreSQL 16** (producción) con **SQLAlchemy** ORM.  
Migraciones gestionadas con **Alembic**.

En desarrollo local sin DB disponible, el sistema usa **repositorios in-memory**
con la misma interfaz (ports).

---

## Modelos

### CardModel — Tabla `cards`

Almacena escenarios generados.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `card_id` | `String` | **PK** | UUID generado con `uuid4()` |
| `owner_id` | `String` | No | Username del creador |
| `visibility` | `String` | No | `"private"` / `"shared"` / `"public"` |
| `shared_with` | `JSON` | Sí | Lista de usernames con acceso |
| `mode` | `String` | No | `"casual"` / `"narrative"` / `"matched"` |
| `seed` | `Integer` | No | Seed determinista (0–2³¹−1) |
| `table_width` | `Integer` | No | Ancho de mesa en mm |
| `table_height` | `Integer` | No | Alto de mesa en mm |
| `table_unit` | `String` | Sí | Unidad original (cm/in/ft) |
| `map_spec` | `JSON` | No | Especificación completa del mapa (shapes) |
| `name` | `String` | Sí | Nombre del escenario |
| `armies` | `String` | Sí | Descripción de ejércitos |
| `deployment` | `String` | Sí | Tipo de despliegue |
| `layout` | `String` | Sí | Tipo de layout |
| `objectives` | `JSON` | Sí | Objetivos (str o dict) |
| `initial_priority` | `String` | Sí | Prioridad inicial |
| `special_rules` | `JSON` | Sí | Lista de reglas especiales |
| `created_at` | `DateTime(UTC)` | No | Timestamp de creación |
| `updated_at` | `DateTime(UTC)` | No | Timestamp de última modificación |

---

### UserModel — Tabla `users`

Almacena credenciales y perfil de usuarios.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `username` | `String` | **PK** | Username único (3–32 chars) |
| `password_hash` | `LargeBinary` | No | Hash PBKDF2-HMAC-SHA256 |
| `salt` | `LargeBinary` | No | Salt único (16 bytes) |
| `name` | `String` | Sí | Nombre para mostrar |
| `email` | `String(unique)` | Sí | Email único |
| `created_at` | `DateTime(UTC)` | No | Timestamp de registro |

**Seguridad:**
- `password_hash` y `salt` son `LargeBinary`, no `String`.
- El hash se calcula con PBKDF2 (600K iteraciones).
- Email tiene constraint `UNIQUE`.

---

### SessionModel — Tabla `sessions`

Gestiona sesiones de usuario con soft-revocation.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `session_id` | `String(64)` | **PK** | Token generado con `secrets` |
| `username` | `String` | No | FK lógica a `users.username` |
| `created_at` | `DateTime(UTC)` | No | Timestamp de creación |
| `last_seen_at` | `DateTime(UTC)` | No | Última actividad |
| `expires_at` | `DateTime(UTC)` | No | Expiración de la sesión |
| `csrf_token` | `String` | No | Token CSRF vinculado |
| `reauth_at` | `DateTime(UTC)` | Sí | Última re-autenticación |
| `revoked_at` | `DateTime(UTC)` | Sí | Soft-revocation (logout) |

**Índices:**
- `ix_sessions_expires_at` — para limpieza de sesiones expiradas.
- `ix_sessions_revoked_at` — para filtrar sesiones activas.

**Soft-revocation:** El logout no elimina el registro, sino que marca `revoked_at`.
Esto permite auditoría y previene race conditions.

---

### FavoritesModel — Tabla `favorites`

Relación many-to-many entre usuarios y cards.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `actor_id` | `String` | **PK (compuesta)** | Username del usuario |
| `card_id` | `String` | **PK (compuesta)** | ID de la card |
| `created_at` | `DateTime(UTC)` | No | Timestamp de marcado |

**Primary Key compuesta:** `(actor_id, card_id)` — un usuario solo puede marcar
una card como favorita una vez.

---

## Diagrama ER

```
┌──────────────┐     ┌──────────────┐
│    users      │     │   sessions   │
├──────────────┤     ├──────────────┤
│ username (PK)│◄────│ username     │
│ password_hash│     │ session_id(PK│
│ salt         │     │ csrf_token   │
│ name         │     │ expires_at   │
│ email (UQ)   │     │ revoked_at   │
│ created_at   │     │ reauth_at    │
└──────┬───────┘     └──────────────┘
       │
       │ owner_id
       ▼
┌──────────────┐     ┌──────────────┐
│    cards      │     │  favorites   │
├──────────────┤     ├──────────────┤
│ card_id (PK) │◄────│ card_id (PK) │
│ owner_id     │     │ actor_id (PK)│
│ visibility   │     │ created_at   │
│ shared_with  │     └──────────────┘
│ mode         │
│ seed         │
│ table_*      │
│ map_spec     │
│ objectives   │
│ special_rules│
│ created_at   │
│ updated_at   │
└──────────────┘
```

---

## Migraciones (Alembic)

### Comandos

```bash
# Crear nueva migración
alembic revision --autogenerate -m "Add column X to table Y"

# Aplicar todas las migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver estado actual
alembic current

# Ver historial
alembic history
```

### Convenciones

- Cada migración tiene un mensaje descriptivo.
- Las migraciones son **reversibles** (down método implementado).
- Se ejecutan automáticamente en Docker al iniciar el contenedor.
- En desarrollo local, se ejecutan manualmente.

---

## Dual Backend

El sistema soporta dos backends de persistencia con la misma interfaz:

| Backend | Uso | Implementación |
|---------|-----|----------------|
| In-memory | Desarrollo, tests | `InMemoryCardRepository`, `InMemoryFavoritesRepository` |
| PostgreSQL | Producción | `PostgresCardRepository`, `PostgresFavoritesRepository` |

La selección ocurre en `bootstrap.py`:
- Si `DATABASE_URL` está configurada y `APP_ENV=prod` → PostgreSQL.
- Si no → fallback a in-memory con log de warning.

### Ports (interfaces)

```python
class CardRepository(Protocol):
    def save(self, card: Card) -> None: ...
    def get_by_id(self, card_id: str) -> Optional[Card]: ...
    def find_by_seed(self, seed: int) -> ...: ...
    def delete(self, card_id: str) -> bool: ...
    def list_all(self) -> ...: ...
    def list_for_owner(self, owner_id: str) -> ...: ...

class FavoritesRepository(Protocol):
    def is_favorite(self, actor_id: str, card_id: str) -> bool: ...
    def set_favorite(self, actor_id: str, card_id: str, value: bool) -> None: ...
    def list_favorites(self, actor_id: str) -> list[str]: ...
    def remove_all_for_card(self, card_id: str) -> None: ...
```

Tanto in-memory como PostgreSQL implementan estos protocols.

---

## Timestamps

Todos los timestamps usan **UTC** (`datetime.now(timezone.utc)`) para evitar
problemas de zona horaria. La conversión a zona local es responsabilidad del
cliente.
