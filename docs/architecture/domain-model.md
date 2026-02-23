# Modelo de Dominio

## Entidades y Value Objects

Todos los modelos de dominio son **frozen dataclasses** (inmutables) con validación
en `__post_init__`.

---

## Card — Entidad principal

```python
@dataclass(frozen=True)
class Card:
    card_id: str
    owner_id: str
    visibility: Visibility          # PRIVATE | SHARED | PUBLIC
    shared_with: Optional[Collection[str]]
    mode: GameMode                  # CASUAL | NARRATIVE | MATCHED
    seed: int                       # 0 = manual, 1–2³¹−1 = seeded
    table: TableSize
    map_spec: MapSpec
    # Opcionales
    name: Optional[str]
    armies: Optional[str]
    deployment: Optional[str]
    layout: Optional[str]
    objectives: Optional[str | dict]
    initial_priority: Optional[str]
    special_rules: Optional[list[dict]]
    seed_attempt: Optional[int]
    generator_version: Optional[str]
```

### Invariantes validados en construcción

| Invariante | Error si falla |
|-----------|----------------|
| `card_id` y `owner_id` son strings no vacíos | `ValidationError` |
| `seed` es int ≥ 0, no es bool | `ValidationError` |
| `table` es `TableSize`, `map_spec` es `MapSpec` | `ValidationError` |
| `visibility` es `Visibility`, `mode` es `GameMode` | `ValidationError` |
| `map_spec.table` coincide con `table` | `ValidationError` |
| `objectives` es None, str, o dict con clave `"objective"` | `ValidationError` |
| `special_rules` es None o list de dicts con campo `"name"` | `ValidationError` |
| `shared_with` no vacío requiere `Visibility.SHARED` | `ValidationError` |

### Métodos de autorización

```python
card.can_user_read(user_id)   # Delega a authz.can_read
card.can_user_write(user_id)  # Delega a authz.can_write (owner-only)
```

---

## TableSize — Value Object

Dimensiones de mesa almacenadas internamente en **milímetros** (int).

```python
@dataclass(frozen=True)
class TableSize:
    width_mm: int    # 600–3000 (60–300 cm)
    height_mm: int   # 600–3000 (60–300 cm)
```

### Conversiones y presets

| Factory | Conversión |
|---------|-----------|
| `TableSize.from_cm(w, h)` | cm × 10 → mm |
| `TableSize.from_in(w, h)` | in × 25 → mm (1 in = 2.5 cm) |
| `TableSize.from_ft(w, h)` | ft × 300 → mm (1 ft = 30 cm) |
| `TableSize.standard()` | 120 × 120 cm (1200 × 1200 mm) |
| `TableSize.massive()` | 180 × 120 cm (1800 × 1200 mm) |

Propiedades: `area_mm2`, `width_cm`, `height_cm`, `preset_name`.

### Restricciones de validación

- Mínimo: 60 cm (600 mm) por lado.
- Máximo: 300 cm (3000 mm) por lado.
- Máximo 2 decimales en cm.
- Rechaza comas como separador decimal.
- Rechaza floats con pérdida de precisión.

---

## MapSpec — Value Object

```python
@dataclass(frozen=True)
class MapSpec:
    table: TableSize
    shapes: list[dict]                       # Scenography shapes
    objective_shapes: list[dict] | None      # Objective markers
    deployment_shapes: list[dict] | None     # Deployment zones (max 4)
```

### Validaciones post-init

- `shapes` no puede ser None; cada shape debe estar dentro de los bounds de la mesa.
- Balance de escenografía (mezcla sólida/pasable).
- Deployment shapes: máximo 4; deben ser border XOR corner.
- Objective shapes validadas contra la geometría de la mesa.

### Shapes soportadas

| Tipo | Campos requeridos |
|------|-------------------|
| `rect` | `x`, `y`, `width`, `height` — dentro de bounds `(0, 0, table.width, table.height)` |
| `circle` | `cx`, `cy`, `r` — centro + radio dentro de bounds |

---

## ScenarioCard — Value Object (generado)

```python
@dataclass(frozen=True)
class ScenarioCard:
    id: str
    mode: GameMode
    seed: int
    layout: CardItem
    deployment: CardItem
    objective: CardItem
    twist: Optional[CardItem]
    story_hook: Optional[CardItem]
    constraints: List[CardItem]
    owner_id: str
    visibility: Visibility
```

Representa un escenario **completo generado** a partir de un seed, con todos los
elementos de contenido MESBG seleccionados aleatoriamente de forma determinista.

---

## CardItem — Value Object (contenido)

```python
@dataclass(frozen=True)
class CardItem:
    id: str
    title: str
    description: str
    tags: List[str]
    modes: List[str]             # ["casual", "narrative", "matched"]
    weights: Dict[str, int]      # {"casual": 1, "matched": 2}
    risk_flags: List[str]        # Penalizan matched_score
    map_spec: Optional[dict]     # Datos geométricos opcionales
```

Los `CardItem` se cargan desde ficheros JSON en `content/mesbg/` y representan
las "piezas" seleccionables del generador: layouts, deployments, objectives,
twists, story hooks y constraints.

---

## Seed — Generación determinista

```python
MAX_SEED = 2_147_483_647  # 2³¹ − 1

def get_rng(seed: int) -> random.Random
def normalize_seed(raw) -> int
def derive_attempt_seed(base_seed: int, attempt_index: int) -> int
```

- `normalize_seed` acepta int ≥ 0, str numérica, float entera; rechaza bool/negativo.
- `derive_attempt_seed` usa SHA-256 para derivar seeds en reintentos; index 0 devuelve base.
- El RNG es `random.Random` (no criptográfico) — determinismo, no seguridad.

---

## Scoring

```python
def matched_score(risk_flags: Iterable[str]) -> int:
    """100 − (10 × len(risk_flags)), mínimo 0."""
```

Cada `risk_flag` en un `CardItem` penaliza la puntuación en modo **matched**
para desincentivar combinaciones desequilibradas.

---

## Constraints

```python
def incompatible_pairs_ok(selected_ids, pairs) -> bool:
    """True si ningún par incompatible está simultáneamente seleccionado."""
```

Se usa durante la generación para validar que las constraints seleccionadas
no creen conflictos lógicos (ej.: "no shooting" + "shooting bonus").

---

## Visibility y AuthZ

```python
class Visibility(Enum):
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"
```

### Reglas de acceso (deny-by-default)

| Operación | Owner | shared_with | Autenticado | Anónimo |
|-----------|-------|-------------|-------------|---------|
| read (PRIVATE) | ✅ | ❌ | ❌ | ❌ |
| read (SHARED) | ✅ | ✅ | ❌ | ❌ |
| read (PUBLIC) | ✅ | ✅ | ✅ | ❌ |
| write | ✅ | ❌ | ❌ | ❌ |

Cualquier ruta no cubierta ⇒ `False` (denegado).

---

## Errores de dominio

```python
class DomainError(Exception): ...
class ValidationError(DomainError): ...     # Input inválido / invariante roto
class NotFoundError(DomainError): ...       # Entidad no encontrada
class ForbiddenError(DomainError): ...      # Permisos insuficientes
```

Los errores de dominio **nunca** contienen códigos HTTP.  
El mapeo a HTTP ocurre exclusivamente en los adapters.
