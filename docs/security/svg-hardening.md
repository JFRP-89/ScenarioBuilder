# Seguridad SVG — Hardening XSS/XXE

## Contexto

Scenario Builder genera documentos SVG que se renderan en el navegador del usuario.  
SVG es un subconjunto de XML capaz de ejecutar JavaScript, lo que lo convierte en
un vector de ataque para XSS y XXE si no se sanitiza correctamente.

---

## Amenazas

### XSS via SVG

Un atacante podría inyectar JavaScript en atributos o elementos SVG:

```xml
<!-- Ataque: script inline -->
<svg><script>alert('XSS')</script></svg>

<!-- Ataque: event handler -->
<svg><rect onclick="alert('XSS')"/></svg>

<!-- Ataque: foreignObject -->
<svg><foreignObject><body onload="alert('XSS')"/></foreignObject></svg>
```

### XXE (XML External Entity)

```xml
<!DOCTYPE svg [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<svg>&xxe;</svg>
```

---

## Controles implementados

### 1. defusedxml

Reemplaza `xml.etree.ElementTree` con `defusedxml` en el parsing:

- **DTD deshabilitados**: no se procesan `DOCTYPE` ni entities externas.
- **Entity expansion deshabilitada**: previene billion laughs attack.
- **External references bloqueadas**: sin acceso a archivos/URLs.

### 2. Allowlist de tags SVG

Solo se permiten tags conocidos y seguros:

```
svg, g, rect, circle, ellipse, line, polyline, polygon, path,
text, tspan, defs, use, clipPath, marker, pattern, linearGradient,
radialGradient, stop, title, desc
```

**Tags bloqueados explícitamente:**
- `<script>` — ejecución de JavaScript
- `<foreignObject>` — incrustación de HTML
- `<iframe>` — carga de contenido externo
- `<object>`, `<embed>` — plugins

### 3. Allowlist de atributos

Solo atributos de presentación y geometría:

```
x, y, width, height, cx, cy, r, rx, ry, d, points,
fill, stroke, stroke-width, opacity, transform,
font-family, font-size, text-anchor, dominant-baseline,
viewBox, xmlns, id, class, clip-path, marker-end
```

**Atributos bloqueados:**
- `on*` (onclick, onload, onerror...) — event handlers
- `href` con `javascript:` — XSS via links
- `xlink:href` con valores dinámicos no validados

### 4. Content-Type forzado

```http
Content-Type: image/svg+xml
```

Previene que el navegador interprete el SVG como HTML.

### 5. Generación interna

El SVG se genera **programáticamente** en el servidor, nunca desde input del usuario:

```python
# infrastructure/maps/svg_map_renderer.py
# El SVG se construye capa por capa con valores calculados:
# bg → grid → zones → terrain → markers → labels → frame
```

Los únicos datos que influyen en el SVG son:
- Dimensiones de mesa (validadas por dominio: 60–300 cm)
- Shapes (generadas internamente con RNG seeded)
- Unidades de display (cm/in/ft — enum validado)

---

## Validación por capas

| Capa | Qué valida |
|------|-----------|
| Domain | Dimensiones de mesa (rango, precisión), shapes (bounds, tipos) |
| Application | actor_id, card_id, render_mode, display_units |
| Infrastructure | Sanitización SVG, defusedxml |
| Adapter | Content-Type header, CSP header (futuro) |

---

## Tests de seguridad SVG

- Tests unitarios de sanitización de tags/atributos.
- Tests de que `<script>` y `foreignObject` se eliminan.
- Tests de que event handlers (`onclick`) se eliminan.
- Tests de Content-Type correcto en response.
