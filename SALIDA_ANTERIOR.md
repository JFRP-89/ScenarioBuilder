Checklist:
- [x] 10.1 Root (lista de archivos)
- [x] 10.2 GitHub (workflow + PR template)
- [x] 10.3 Docs
- [x] 10.4 Context (troceado)
- [x] 10.5 Content JSON (2–3 items por archivo; modes incluyen matched; nunca usar balanced)
- [x] 10.6 Código (stubs sin lógica en adaptadores)
- [x] 10.7 Tests (unit + integration/e2e placeholders)
- [x] 11 Entrega (árbol + ficheros críticos + JSON + tests + backlog semana 1)

Árbol (alto nivel):
- [README.md](README.md)
- [AGENTS.md](AGENTS.md)
- [CHANGELOG.md](CHANGELOG.md)
- [requirements.txt](requirements.txt)
- [.env.example](.env.example)
- [Dockerfile](Dockerfile)
- [docker-compose.yml](docker-compose.yml)
- [Makefile](Makefile)
- [slides/README.md](slides/README.md)
- [.github/workflows/ci.yml](.github/workflows/ci.yml)
- [.github/pull_request_template.md](.github/pull_request_template.md)
- [docs/](docs/)
- [context/](context/)
- [content/mesbg/](content/mesbg/)
- [src/](src/)
- [tests/](tests/)
- [BACKLOG_SEMANA_1.md](BACKLOG_SEMANA_1.md)

Ficheros críticos creados:
- [README.md](README.md)
- [AGENTS.md](AGENTS.md)
- [CHANGELOG.md](CHANGELOG.md)
- [requirements.txt](requirements.txt)
- [.env.example](.env.example)
- [docker-compose.yml](docker-compose.yml)
- [.github/workflows/ci.yml](.github/workflows/ci.yml)
- [.github/pull_request_template.md](.github/pull_request_template.md)
- [docs/deploy/runbook.md](docs/deploy/runbook.md)
- [Makefile](Makefile)

JSON de contenido MESBG:
- [content/mesbg/layouts.json](content/mesbg/layouts.json)
- [content/mesbg/deployments.json](content/mesbg/deployments.json)
- [content/mesbg/objectives.json](content/mesbg/objectives.json)
- [content/mesbg/twists.json](content/mesbg/twists.json)
- [content/mesbg/story_hooks.json](content/mesbg/story_hooks.json)
- [content/mesbg/constraints.json](content/mesbg/constraints.json)
- [content/mesbg/matched_heuristics.json](content/mesbg/matched_heuristics.json)

Tests unitarios iniciales:
- [tests/unit/test_seed_determinism.py](tests/unit/test_seed_determinism.py)
- [tests/unit/test_constraints_incompatible_pairs.py](tests/unit/test_constraints_incompatible_pairs.py)
- [tests/unit/test_scoring_matched_penalizes_risk.py](tests/unit/test_scoring_matched_penalizes_risk.py)
- [tests/unit/test_map_spec_validation.py](tests/unit/test_map_spec_validation.py)
- [tests/unit/test_table_presets.py](tests/unit/test_table_presets.py)
- [tests/unit/test_application_use_cases.py](tests/unit/test_application_use_cases.py)

Backlog Semana 1:
- [BACKLOG_SEMANA_1.md](BACKLOG_SEMANA_1.md)

Tabla de evidencia:
| Requisito | Evidencia (ruta + referencia) | OK/NO |
|---|---|---|
| Root files | [README.md](README.md), [AGENTS.md](AGENTS.md), [CHANGELOG.md](CHANGELOG.md), [requirements.txt](requirements.txt), [.env.example](.env.example), [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml), [Makefile](Makefile) | OK |
| CI/PR template | [.github/workflows/ci.yml](.github/workflows/ci.yml), [.github/pull_request_template.md](.github/pull_request_template.md) | OK |
| Docs | [docs/](docs/) | OK |
| Context | [context/](context/) | OK |
| Content JSON | [content/mesbg/](content/mesbg/) | OK |
| Código | [src/](src/) | OK |
| Tests | [tests/](tests/) | OK |
| Backlog semana 1 | [BACKLOG_SEMANA_1.md](BACKLOG_SEMANA_1.md) | OK |

Si quieres, puedo volcar el contenido completo de cualquier archivo.
