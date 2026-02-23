# Renderizado SVG — Pipeline de mapas

## Visión general

El motor de renderizado SVG genera mapas tácticos vectoriales a escala real
con un pipeline de 7 capas, implementado en `infrastructure/maps/`.

---

## Arquitectura del renderer

```
MapRenderer (port)
    │
    └── SvgMapRenderer (infrastructure)
            │
            └── _renderer/ (sub-package)
                ├── _geometry.py        Cálculos geométricos
                ├── _primitives.py      Elementos SVG base (rect, circle, path)
                ├── _tactical_defs.py   Definiciones (gradients, patterns, markers)
                ├── _overlay.py         Cotas + brújula
                ├── _sanitize.py        Sanitización de SVG
                └── __init__.py         Re-exports
```

## Pipeline de 7 capas

El SVG se construye capa por capa, de atrás hacia adelante:

```
┌─────────────────────────────────────────┐
│ 7. Frame        Marco con bordes        │
├─────────────────────────────────────────┤
│ 6. Labels       Etiquetas de zonas      │
├─────────────────────────────────────────┤
│ 5. Markers      Indicadores de objetivo │
├─────────────────────────────────────────┤
│ 4. Terrain      Escenografía (shapes)   │
├─────────────────────────────────────────┤
│ 3. Zones        Deployment zones        │
├─────────────────────────────────────────┤
│ 2. Grid         Cuadrícula de referencia│
├─────────────────────────────────────────┤
│ 1. Background   Fondo de mesa           │
└─────────────────────────────────────────┘
```

### Capa 1: Background

Rectángulo base con el color de la mesa. Dimensiones exactas de la `TableSize`.

### Capa 2: Grid

Cuadrícula de referencia con líneas finas (opacidad baja) para orientación
espacial. Ajustada a las dimensiones de la mesa.

### Capa 3: Zones (Deployment)

Zonas de despliegue para cada ejército:
- Máximo 4 deployment shapes.
- Restricción: border XOR corner (no mezclar).
- Coloreadas por ejército con transparencia.

### Capa 4: Terrain (Scenography)

Shapes de escenografía generadas por el motor determinista:
- **Sólidas**: Terreno impasable (edificios, rocas).
- **Pasables**: Terreno transitable (bosques, colinas).
- Balance validado en `MapSpec.__post_init__`.
- Tipos: `rect` y `circle`.

### Capa 5: Markers

Indicadores de objetivos sobre el mapa.

### Capa 6: Labels

Etiquetas identificativas para zonas de despliegue y puntos de interés.

### Capa 7: Frame (Overlay)

Capa superior con:
- **Cotas (acotaciones)**: Dimensiones exactas en cm/in/ft en los 4 bordes.
- **Brújula**: Indicador cardinal (N/S/E/W) en esquina.

---

## Port y contrato

```python
class MapRenderer(Protocol):
    def render_svg(self, map_spec: dict) -> str: ...
    def render(
        self,
        table_mm: tuple,
        shapes: list,
        render_mode: str = "full",
        display_units: str = "cm"
    ) -> str: ...
```

### Parámetros de renderizado

| Parámetro | Valores | Descripción |
|-----------|---------|-------------|
| `render_mode` | `"full"` | Renderizado completo (7 capas) |
| `display_units` | `"cm"`, `"in"`, `"ft"` | Unidades de las cotas |

---

## Shapes

### Rectángulo

```json
{
  "type": "rect",
  "x": 100,
  "y": 200,
  "width": 150,
  "height": 80,
  "passable": false
}
```

Validación: `x + width ≤ table_width`, `y + height ≤ table_height`.

### Círculo

```json
{
  "type": "circle",
  "cx": 500,
  "cy": 300,
  "r": 50,
  "passable": true
}
```

Validación: `cx - r ≥ 0`, `cx + r ≤ table_width`, análogo para Y.

---

## Unidades y escala

| Unidad | Factor (respecto a cm) | Uso principal |
|--------|----------------------|---------------|
| cm | 1.0 | Estándar métrico |
| in (inches) | 1 in = 2.5 cm | Sistema imperial USA |
| ft (feet) | 1 ft = 30 cm | Mesas grandes |

Las dimensiones internas son siempre en **milímetros** (enteros).  
La conversión a unidades de display ocurre solo en el renderizado de cotas.

---

## Tema visual

El renderer usa un tema **"Tactical Dark"** coherente con el resto de la UI:

- Fondo de mesa con color oscuro (`#1a1a2e`-like)
- Grid con opacidad baja (0.1-0.2)
- Deployment zones con colores de ejército translúcidos
- Terreno con texturas diferenciadas (sólido vs pasable)
- Cotas con fuente clara sobre fondo oscuro
- Brújula estilizada con acento dorado

---

## Seguridad

- SVG generado internamente, nunca desde input del usuario.
- `defusedxml` para cualquier parsing de XML.
- Allowlist de tags y atributos (ver [SVG Hardening](../security/svg-hardening.md)).
- Content-Type forzado a `image/svg+xml`.
