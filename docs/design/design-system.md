# Sistema de Diseño — Tactical Dark

## Visión general

Scenario Builder usa un sistema de diseño oscuro y táctico denominado
**"Tactical Dark"**, implementado en dos archivos CSS según el adapter:

| Archivo | Adapter | Uso |
|---------|---------|-----|
| `tactical.css` | Flask/Jinja templates | Design tokens, componentes HTML |
| `tactical_gradio.css` | Gradio UI | Override del tema default de Gradio |

---

## Design Tokens

Todos los tokens usan el namespace `--sb-*` para evitar colisiones.

### Colores base

| Token | Valor | Uso |
|-------|-------|-----|
| `--sb-bg` | `#0d1117` | Fondo principal |
| `--sb-bg-card` | `#161b22` | Fondo de tarjetas |
| `--sb-bg-input` | `#1c2128` | Fondo de inputs |
| `--sb-text` | `#e9eef6` | Texto principal |
| `--sb-text-muted` | `#8b949e` | Texto secundario |
| `--sb-border` | `#30363d` | Bordes |

### Colores de acento

| Token | Valor | Uso |
|-------|-------|-----|
| `--sb-accent` | `#f6d41c` | Acento dorado/ámbar (primary) |
| `--sb-accent-hover` | `#e5c518` | Hover del acento |
| `--sb-success` | `#3fb950` | Estados exitosos |
| `--sb-danger` | `#ef5f62` | Errores, acciones destructivas |
| `--sb-danger-bg` | `#2a1215` | Fondo de alertas de error |
| `--sb-warning` | `#d29922` | Advertencias |

### Tipografía

| Token | Valor | Uso |
|-------|-------|-----|
| `--sb-font` | `'Inter', system-ui, sans-serif` | Familia tipográfica |
| `--sb-font-mono` | `'JetBrains Mono', monospace` | Código, seeds |
| `--sb-text-sm` | `0.875rem` | Texto pequeño |
| `--sb-text-base` | `1rem` | Texto base |
| `--sb-text-lg` | `1.125rem` | Texto grande |
| `--sb-text-xl` | `1.5rem` | Títulos |

### Espaciado y layout

| Token | Valor | Uso |
|-------|-------|-----|
| `--sb-radius` | `6px` | Border radius base |
| `--sb-radius-lg` | `12px` | Radius para tarjetas |
| `--sb-spacing-xs` | `4px` | Espaciado mínimo |
| `--sb-spacing-sm` | `8px` | Espaciado pequeño |
| `--sb-spacing-md` | `16px` | Espaciado medio |
| `--sb-spacing-lg` | `24px` | Espaciado grande |

---

## Componentes (Flask/Jinja)

Implementados como **macros Jinja** en `templates/macros.html` y clases CSS
en `tactical.css`.

### Botones (`.sb-btn`)

```html
{{ sb_btn("Guardar", variant="primary") }}
{{ sb_btn("Cancelar", variant="secondary") }}
{{ sb_btn("Eliminar", variant="danger") }}
```

| Variante | Color base | Hover |
|----------|-----------|-------|
| `primary` | `--sb-accent` (dorado) | `--sb-accent-hover` |
| `secondary` | Transparente + borde | Fondo sutil |
| `danger` | `--sb-danger` | Darkened |

### Tarjetas (`.sb-card`)

```html
{{ sb_card(title="Escenario #42", content="...", footer="...") }}
```

- Fondo: `--sb-bg-card`
- Borde: `--sb-border`
- Border radius: `--sb-radius-lg`
- Hover: Borde accent con transición 0.2s

### Inputs (`.sb-input`)

```html
{{ sb_input(name="seed", label="Seed", type="number") }}
{{ sb_input_hinted(name="email", label="Email", hint="tu@email.com") }}
```

- Fondo: `--sb-bg-input`
- Borde: `--sb-border`, focus → `--sb-accent`
- Placeholder: `--sb-text-muted`

### Seed Display (`.sb-seed`)

```html
{{ sb_seed_display(seed=42) }}
```

- Fuente monoespaciada (`--sb-font-mono`)
- Tamaño prominente
- Elemento `<button>` (accesible, focusable)
- `:focus-visible` outline visible

### Screen Reader Only (`.sb-sr-only`)

```css
.sb-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}
```

Oculta visualmente pero mantiene accesible para lectores de pantalla.

---

## Tema Gradio (tactical_gradio.css)

Override del tema default de Gradio para mantener consistencia visual.

### Estructura de secciones

1. **Root**: Variables CSS Gradio remapeadas a tokens `--sb-*`
2. **Container**: Fondo, márgenes, padding del layout principal
3. **Inputs**: Selectores, textareas, dropdowns con tema oscuro
4. **Buttons**: Primary (dorado), secondary, cancel (rojo/danger)
5. **Tabs**: Navegación tabulada con acento
6. **Cards/Panels**: Accordion, group, panel con fondo card
7. **SVG Preview**: Contendedor del mapa con aspect-ratio
8. **Status indicators**: Badges de visibilidad, modo, scoring
9. **Control Bar**: Barra de controles segmentada con botones tipo pastilla
10. **Utilities**: Helpers, responsive, animaciones

### Accesibilidad WCAG

- **Contraste mínimo 4.5:1** en texto sobre fondos oscuros.
- Todos los fondos `rgba()` reemplazados por **opacos** para contraste calculable:
  - Error: `#ef5f62` sobre `#2a1215` (ratio 5.8:1)
  - Warning: `#f6d41c` sobre `#252619` (ratio 8.2:1)
  - Code: `#f6d41c` sobre `#2d302a` (ratio 7.1:1)
- `letter-spacing` sin `!important` (permite override por usuario).
- `:focus-visible` en todos los elementos interactivos.
- Roles ARIA mantenidos por Gradio.

---

## Convenciones

### Naming

- **Tokens**: `--sb-<categoria>-<variante>` (ej. `--sb-bg-card`)
- **Clases**: `.sb-<componente>` (ej. `.sb-btn`, `.sb-card`)
- **Variantes**: `.sb-<componente>--<variante>` (ej. `.sb-btn--danger`)
- **Estados**: `.sb-<componente>--active`, `--disabled`

### Organización del CSS

```
/* === SECTION 1: Reset & Variables === */
/* === SECTION 2: Layout === */
/* === SECTION 3: Typography === */
/* === SECTION 4: Components === */
/* === SECTION 5: Utilities === */
/* === SECTION 6: Responsive === */
```

### No duplicar selectores

Cada selector CSS aparece **una sola vez** en el archivo.
Si se necesita extender, añadir propiedades al bloque existente.
(Validado por SonarQube).
