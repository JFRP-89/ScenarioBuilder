# Política de Imports

## Regla general

Las dependencias **solo fluyen hacia dentro** (de capas externas a internas).

```
domain/         → (nada)
application/    → domain/
infrastructure/ → domain/ + application/
adapters/       → domain/ + application/ + infrastructure/
```

## Prohibiciones explícitas

| Desde | Hacia | ¿Permitido? |
|-------|-------|-------------|
| `domain/` | `application/` | ❌ Nunca |
| `domain/` | `infrastructure/` | ❌ Nunca |
| `domain/` | `adapters/` | ❌ Nunca |
| `application/` | `infrastructure/` | ❌ Nunca |
| `application/` | `adapters/` | ❌ Nunca |
| `infrastructure/` | `adapters/` | ❌ Nunca |

## Prefijo `src.` prohibido

```python
# ❌ Prohibido
from src.domain.cards.card import Card

# ✅ Correcto
from domain.cards.card import Card
```

El `PYTHONPATH` apunta a `src/`, por lo que los imports parten directamente
del nombre del paquete (`domain`, `application`, `infrastructure`, `adapters`).

## Imports circulares

Si se detecta un import circular:

1. **Preferido**: reestructurar en un módulo de tipos (`types.py` o `_types.py`).
2. **Aceptable**: usar `TYPE_CHECKING` guard:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.cards.card import Card
```

## Orden de imports (isort)

```python
# 1. stdlib
import os
from datetime import datetime

# 2. third-party
import gradio as gr
from flask import Blueprint

# 3. project (first-party)
from domain.cards.card import Card
from application.ports.repositories import CardRepository
```

Configurado en `pyproject.toml` con `isort` (first-party = `src`).

## Validación

- **CI**: `ruff check .` detecta imports no usados (`F401`) y errores de orden.
- **Test**: `test_domain_imports.py` verifica que `domain/` no importa de capas externas.
- **Pylint**: Configurado para respetar `mypy_path = "src"`.
