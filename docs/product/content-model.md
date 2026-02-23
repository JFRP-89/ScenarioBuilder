# Contenido MESBG — Modelo de datos

## Visión general

El contenido del juego MESBG (Middle Earth Strategy Battle Game) se almacena en
archivos JSON en `content/mesbg/` y se carga mediante el `ContentProvider` port.

---

## Archivos de contenido

| Archivo | Descripción | Selección |
|---------|-------------|-----------|
| `layouts.json` | Disposiciones de mesa (terrain layouts) | 1 por escenario |
| `deployments.json` | Tipos de despliegue (zonas de entrada) | 1 por escenario |
| `objectives.json` | Misiones y condiciones de victoria | 1 por escenario |
| `twists.json` | Giros narrativos (solo modo narrative) | 0–1 por escenario |
| `story_hooks.json` | Hooks de historia (solo narrative) | 0–1 por escenario |
| `constraints.json` | Restricciones especiales de juego | 0–N por escenario |
| `matched_heuristics.json` | Heurísticas de balance para matched | Scoring |

---

## Estructura de un CardItem

Cada elemento de contenido sigue el esquema `CardItem`:

```json
{
  "id": "layout-open-field",
  "title": "Open Field",
  "description": "A vast open field with minimal terrain...",
  "tags": ["open", "flat", "simple"],
  "modes": ["casual", "narrative", "matched"],
  "weights": {
    "casual": 1,
    "narrative": 1,
    "matched": 2
  },
  "risk_flags": [],
  "map_spec": {
    "shapes": [...]
  }
}
```

### Campos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `id` | string | ✅ | Identificador único (ej. `"constraint-limited-shooting"`) |
| `title` | string | ✅ | Nombre legible (ej. `"Limited Shooting"`) |
| `description` | string | ✅ | Descripción textual |
| `tags` | string[] | ✅ | Etiquetas para categorización |
| `modes` | string[] | ✅ | Modos en los que está disponible |
| `weights` | dict[str, int] | ✅ | Peso por modo (mayor = más probable) |
| `risk_flags` | string[] | ❌ | Flags que penalizan `matched_score` |
| `map_spec` | dict | ❌ | Datos geométricos para el layout (si aplica) |

### Weights

Los weights determinan la probabilidad de selección por modo:

```json
"weights": {
  "casual": 1,     // Peso normal
  "narrative": 2,  // Doble probabilidad en narrative
  "matched": 0     // No disponible en matched
}
```

Un weight de 0 excluye el item de ese modo.

### Risk Flags

Indicadores de que un item puede causar desequilibrio en modo matched:

```json
"risk_flags": ["unbalanced-deployment", "extreme-terrain"]
```

Cada flag reduce el `matched_score` en 10 puntos (desde 100, floor 0).

---

## Pipeline de generación

```
1. ContentProvider carga JSONs desde content/mesbg/
2. generate_card() recibe listas de CardItems
3. RNG seeded (get_rng(seed)) selecciona 1 de cada categoría
4. Constraints se validan con incompatible_pairs_ok()
5. Se construye ScenarioCard con todos los elementos seleccionados
```

### Determinismo

Dado el mismo `seed`, la selección es **siempre idéntica**:

```python
rng = get_rng(42)
layout = rng.choice(layouts)       # Siempre el mismo
deployment = rng.choice(deployments)  # Siempre el mismo
```

Esto permite reproducibilidad perfecta: dos usuarios con seed 42 obtienen
el mismo escenario exacto.

---

## Constraints — Pares incompatibles

Algunas constraints se excluyen mutuamente:

```python
incompatible_pairs = [
    ("constraint-no-shooting", "constraint-shooting-bonus"),
    ("constraint-no-magic", "constraint-magic-enhanced"),
]

incompatible_pairs_ok(selected_ids, incompatible_pairs)
# → False si ambos elementos de un par están seleccionados
```

---

## ContentProvider (port)

```python
class ContentProvider(Protocol):
    def get_layouts(self) -> Iterable[CardItem]: ...
    def get_deployments(self) -> Iterable[CardItem]: ...
    def get_objectives(self) -> Iterable[CardItem]: ...
    def get_twists(self) -> Iterable[CardItem]: ...
    def get_story_hooks(self) -> Iterable[CardItem]: ...
    def get_constraints(self) -> Iterable[CardItem]: ...
```

### FileContentProvider (implementación)

Lee los JSON desde `content/mesbg/` y los parsea a `CardItem`:

```python
class FileContentProvider:
    def __init__(self, base_path: str = "content/mesbg"):
        self.base_path = base_path

    def get_layouts(self) -> list[CardItem]:
        return self._load("layouts.json")
```

---

## Extensibilidad

Para añadir contenido:

1. Editar el JSON correspondiente en `content/mesbg/`.
2. Seguir el esquema `CardItem` (id, title, description, tags, modes, weights).
3. Añadir `risk_flags` si el item puede causar desequilibrio.
4. Opcionalmente añadir `map_spec` con shapes geométricas.

Para añadir un **nuevo juego** (roadmap):

1. Crear carpeta `content/<game>/` con los mismos JSON.
2. Implementar un nuevo `ContentProvider` específico.
3. Registrar en `bootstrap.py`.
