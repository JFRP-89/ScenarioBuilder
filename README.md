# MESBG Scenario Card Generator

Generador de cartas de escenario para Middle-earth Strategy Battle Game (MESBG) con modos `casual`, `narrative` y `matched`.
Incluye generación determinista por `seed` y renderizado de layouts en SVG.

## Stack
- Python 3.11
- Flask (API)
- Gradio (UI consume la API)
- Postgres
- Docker / Docker Compose

## Instalación
```bash
python -m pip install -r requirements.txt
```

## Ejecución
```bash
docker compose up
```

API: http://localhost:8000
UI: http://localhost:7860

## Estructura
```
src/
  domain/          # reglas puras
  application/     # casos de uso + puertos
  infrastructure/  # detalles técnicos
  adapters/        # Flask + Gradio
content/           # JSON editable
docs/              # documentación de evaluación
context/           # conocimiento para IA
tests/             # unit / integration / e2e
```

## Funcionalidades (MVP)
- Generación de cartas por modo y seed
- SVG de mapa desde map_spec
- Guardar, listar y favoritos
- Presets de tamaño (Standard / Massive)

## Despliegue
Pendiente de URL pública. Ver [docs/deploy/runbook.md](docs/deploy/runbook.md).

## Slides
Ver [slides/README.md](slides/README.md).
