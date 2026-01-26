# MESBG Scenario Card Generator

Generador de cartas de escenario para Middle-earth Strategy Battle Game (MESBG) con modos `casual`, `narrative` y `matched`.
Incluye generación determinista por `seed` y renderizado de **board layouts** en **SVG**.

## Stack
- Python 3.11
- Flask (API)
- Gradio (UI consume la API)
- Postgres
- Docker / Docker Compose

## Instalación
    python -m pip install -r requirements.txt

## Ejecución
    docker compose up

- API: http://localhost:8000  
- UI: http://localhost:7860

## Estructura
    src/
      domain/          # reglas puras
      application/     # casos de uso + puertos
      infrastructure/  # detalles técnicos
      adapters/        # Flask + Gradio
    content/           # JSON editable
    docs/              # documentación de evaluación
    context/           # conocimiento para IA
    tests/             # unit / integration / e2e

## Desarrollo
- Crear venv y depender de `python -m pip install -r requirements.txt`.
- Pytest usa `pythonpath = src`; ejecuta `python -m pytest tests/unit -q` para rápido y `python -m pytest tests -q` para completo.
- Formato/estilo: `python -m black --check .` y `python -m ruff check .`.

## Modelos de dominio (MVP)
- `TableSize`: dimensiones de mesa en mm (int); presets `standard()` 120x120 cm y `massive()` 180x120 cm; conversions `from_cm|from_in|from_ft` con redondeo HALF_UP a 0.1 cm y límites 60–300 cm.
- `MapSpec`: valida shapes (`circle`, `rect`, `polygon`) sobre la mesa; límites anti-abuso (<=100 shapes, <=200 puntos por polígono) y coordenadas/medidas int dentro del tablero.
- `Card`: une identidad, ownership/visibility (`Visibility`), modo de juego (`GameMode`: casual/narrative/matched), seed determinista, `TableSize` y `MapSpec`; helpers `can_user_read` / `can_user_write` delegan en AuthZ.

## Funcionalidades (MVP)
- Generación de cartas por modo y seed
- SVG de mapa desde `map_spec`
- Guardar, listar y favoritos
- Presets de tamaño (Standard / Massive)

## Documentación
- Runbook: docs/deploy/runbook.md
- Seguridad: docs/security/threat-model.md
- Slides: slides/README.md

## Despliegue
Pendiente de URL pública. Ver `docs/deploy/runbook.md`.
