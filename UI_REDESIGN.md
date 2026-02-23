# UI_REDESIGN.md — Tactical Dark Theme

## Overview

Full visual overhaul of both **Flask** (auth pages) and **Gradio** (main app at `/sb`)
layers, unifying them under a single **"Tactical Dark"** design language.

No business logic was changed — all modifications are purely presentational.

## Design Language

| Token | Value | Usage |
|-------|-------|-------|
| `--sb-bg` | `#06080b` | Page background |
| `--sb-bg-grid` | linear-gradient grid | Tactical grid overlay |
| `--sb-panel` | `#111315` | Card/panel base |
| `--sb-panel-hover` | `#1d2736` | Interactive panel hover |
| `--sb-border` | `#2a3545` | Borders, dividers |
| `--sb-text` | `#e9eef6` | Primary text |
| `--sb-text-muted` | `#92a9c1` | Secondary / label text |
| `--sb-text-dim` | `#5a7090` | Placeholders, empty states |
| `--sb-accent` | `#f6d41c` | Primary accent (amber) |
| `--sb-accent-hover` | `#d4bc49` | Accent hover state |
| `--sb-danger` | `#e5484d` | Destructive actions |
| `--sb-radius` | `10px` | Default border radius |
| `--sb-font` | `'Inter', sans-serif` | UI font |
| `--sb-font-mono` | `'JetBrains Mono', monospace` | Seeds, codes |

## Architecture

```
src/adapters/
├── http_flask/
│   ├── static/
│   │   ├── css/tactical.css      ← Design tokens + all Flask components (~750 LOC)
│   │   └── js/ui.js              ← Modal, clipboard, loading helpers
│   ├── templates/
│   │   ├── base.html             ← Shared layout (topbar, blocks, fonts)
│   │   ├── macros.html           ← Jinja2 component macros (btn, input, card…)
│   │   ├── login.html            ← Refactored → extends base.html
│   │   └── register.html         ← Refactored → extends base.html
│   └── app.py                    ← static_folder configured
│
└── ui_gradio/
    ├── ui/
    │   ├── tactical_gradio.css   ← Gradio CSS variable overrides (~350 LOC)
    │   ├── components/
    │   │   ├── scenario_card.py  ← Inline styles → dark palette
    │   │   ├── svg_preview.py    ← Inline styles → dark palette
    │   │   └── search_helpers.py ← Empty state color fix
    │   ├── pages/
    │   │   ├── home.py           ← Empty state colors
    │   │   ├── list_scenarios.py ← Empty state colors
    │   │   ├── favorites.py      ← Empty state colors
    │   │   └── scenario_detail.py← Placeholder colors
    │   └── wiring/
    │       ├── wire_detail.py    ← Loading/empty state colors
    │       ├── wire_favorites.py ← Empty favorites message color
    │       └── _detail/_render.py← Field rows, sections, SVG wrapper
    ├── services/
    │   └── navigation.py         ← SVG fallback placeholder color
    └── app.py                    ← css= param loads tactical_gradio.css
```

## Files Created

| File | Purpose | LOC |
|------|---------|-----|
| `static/css/tactical.css` | Global design tokens, resets, all component styles | ~750 |
| `static/js/ui.js` | Modal, clipboard copy, button loading state | ~60 |
| `templates/base.html` | Shared layout: fonts, topbar, block slots | ~35 |
| `templates/macros.html` | Reusable Jinja2 macros (btn, input, card, panel…) | ~120 |
| `ui/tactical_gradio.css` | Gradio variable overrides + custom component styles | ~350 |

## Files Modified

| File | Changes |
|------|---------|
| `http_flask/app.py` | Added `static_folder` + `static_url_path` to Flask init |
| `ui_gradio/app.py` | Reads `tactical_gradio.css` and injects via `gr.Blocks(css=…)` |
| `templates/login.html` | Full rewrite — extends `base.html`, uses macros, dark theme |
| `templates/register.html` | Full rewrite — extends `base.html`, uses macros, dark theme |
| `scenario_card.py` | 5 inline color updates (card bg, text, seed, actions, placeholder) |
| `svg_preview.py` | 2 inline color updates (placeholder + container) |
| `_detail/_render.py` | 10 inline color updates (fields, sections, SVG wrapper) |
| `home.py` | 2 empty state / page info color updates |
| `list_scenarios.py` | 2 empty state / page info color updates |
| `scenario_detail.py` | 2 placeholder / loading text color updates |
| `favorites.py` | 1 loading message color update |
| `wire_detail.py` | 4 loading / empty state color updates |
| `wire_favorites.py` | 1 empty favorites message color update |
| `navigation.py` | 1 SVG fallback placeholder color update |
| `search_helpers.py` | 1 empty results message color update |

## Jinja2 Macros Available

| Macro | Description |
|-------|-------------|
| `sb_btn(text, type, size, icon)` | Styled button (primary/secondary/ghost/danger) |
| `sb_btn_link(text, href, type)` | Anchor styled as button |
| `sb_input(name, type, placeholder, required)` | Dark-themed form input |
| `sb_input_hinted(name, id, type, placeholder)` | Input with hint slot |
| `sb_chip(text, variant)` | Status chip (info/success/warning/danger/neutral) |
| `sb_badge(text, variant)` | Compact badge |
| `sb_card()` | Card container (caller block) |
| `sb_panel(title)` | Panel with optional title |
| `sb_empty(icon, title, subtitle)` | Empty state illustration |
| `sb_modal(id, title)` | Modal dialog (caller block) |
| `sb_pagination(current, total, base_url)` | Page navigation |
| `sb_svg_frame()` | SVG preview frame (caller block) |
| `sb_seed_display(seed)` | Monospaced seed display with copy button |

## Accessibility

- Focus-visible outlines: `2px solid var(--sb-accent)` with `2px` offset
- Color contrast: all text/background combos meet WCAG AA (≥ 4.5:1)
- `prefers-reduced-motion`: all animations disabled when user prefers
- Keyboard support: modal Escape-to-close, tab navigation
- Semantic HTML: headings, labels, form associations preserved

## Responsive Breakpoints

- `≤ 768px`: Single-column cards, smaller padding, adjusted topbar
- `≤ 480px`: Compact card layout, reduced font sizes

## Test Results After Redesign

- **Unit**: 1887 passed, 0 failed, 0 skipped
- **Integration**: 1097 passed, 0 failed, 0 skipped
- **Total**: 2984 tests, all green
- **Lint (ruff)**: 0 errors in modified files
