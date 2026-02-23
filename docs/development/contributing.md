# Guía de Contribución

## Prerrequisitos

1. Leer [AGENTS.md](../../AGENTS.md) — reglas globales del proyecto.
2. Familiarizarse con la [arquitectura](../architecture/overview.md).
3. Setup local completo (ver [local-setup.md](local-setup.md)).
4. Tests verdes antes de empezar.

---

## Workflow de desarrollo

### 1. Crear rama

```bash
git checkout -b feature/<nombre-descriptivo>
# Ejemplo: git checkout -b feature/export-pdf
```

### 2. TDD

```
RED    → Escribir test que falla
GREEN  → Código mínimo para que pase
REFACTOR → Mejorar código, tests verdes
```

### 3. Verificar calidad

```bash
pytest -q                    # All tests pass
ruff check .                 # No lint errors
```

### 4. Actualizar CHANGELOG

Añadir entrada en `## [Unreleased]`:

```markdown
### Added
- Export PDF de escenarios (#42)
```

### 5. Commit

```bash
git add -A
git commit -m "feat: add PDF export for scenario cards"
```

### Convención de commits

```
feat:     Nueva funcionalidad
fix:      Corrección de bug
refactor: Refactorización sin cambio de comportamiento
test:     Nuevos tests o corrección de tests
docs:     Documentación
chore:    Mantenimiento (deps, config)
security: Fix de seguridad
```

---

## Definition of Done

Un PR se considera listo para merge cuando cumple:

### Tests
- [ ] Todos los tests pasan (`pytest -q`)
- [ ] Coverage: domain 100%, application ≥ 80%
- [ ] Nuevos tests para nueva funcionalidad
- [ ] Tests de regresión si es un fix

### Código
- [ ] `ruff check .` limpio
- [ ] Sin imports `src.*`
- [ ] Sin lógica de negocio en adapters
- [ ] Facades < 450 líneas (si aplica)
- [ ] Módulos internos con tests 1:1 (si aplica)

### Arquitectura
- [ ] Reglas de capas respetadas
- [ ] Composition root actualizado (si se añaden nuevos servicios)
- [ ] Ports definidos para nuevas interfaces

### Seguridad
- [ ] Deny-by-default en nuevos endpoints
- [ ] Anti-IDOR en accesos a recursos
- [ ] Input validation con allowlist
- [ ] Sin hardcoded secrets

### Documentación
- [ ] CHANGELOG actualizado
- [ ] Docstrings en funciones públicas
- [ ] AGENTS.md actualizado si hay cambio arquitectural

---

## No-Gos (bloquean merge)

- Tests en rojo
- Errores de ruff
- Imports con `src.`
- Lógica de negocio en adapters
- Domain coverage < 100%
- Secretos hardcoded
- Breaking changes sin documentar

---

## Estructura de tests

```
tests/
├── unit/                    # 60% del total
│   ├── domain/              # 100% coverage obligatorio
│   ├── application/         # ≥80% coverage obligatorio
│   ├── adapters/            # Characterization + wiring tests
│   └── infrastructure/      # Tests de repos, generators
├── integration/             # 30% del total
│   ├── adapters/            # Flask routes, Gradio smoke
│   └── infrastructure/      # Bootstrap, repos con BD
└── e2e/                     # 10% del total
    └── (CRUD flows, authz, security)
```

### Naming de tests

```python
def test_<qué_se_testea>_<escenario>_<resultado_esperado>():
    """Dado <contexto>, cuando <acción>, entonces <resultado>."""
```

Ejemplo:
```python
def test_create_card_with_negative_seed_raises_validation_error():
    """Dado un seed negativo, cuando se crea una Card, entonces lanza ValidationError."""
```

---

## Patrones a seguir

### Nuevo use case

1. Definir port (Protocol) en `application/ports/`
2. Crear Request/Response DTOs
3. Implementar `execute()` en `application/use_cases/`
4. Implementar port en `infrastructure/`
5. Registrar en `bootstrap.py` (composition root)
6. Exponer en adapter (Flask route o Gradio handler)
7. Tests: unit para use case + integration para route

### Nuevo endpoint Flask

1. Crear función en el blueprint apropiado
2. Parsear JSON, extraer `actor_id` del header
3. Llamar `services.<use_case>.execute(request)`
4. Mapear resultado a JSON + status code
5. Tests: integration con `test_client()`

### Nuevo componente Gradio

1. Si facade < 250 líneas: añadir directamente
2. Si facade > 350 líneas: extraer lógica a `_<feature>/`
3. 1 test file por módulo interno extraído
4. Coverage ≥ 80% en módulos internos

---

## Herramientas de calidad

| Herramienta | Propósito | Comando |
|-------------|----------|---------|
| pytest | Testing | `pytest -q` |
| ruff | Lint + format | `ruff check .` |
| mypy | Type checking | `mypy src/` |
| bandit | SAST (seguridad) | `bandit -r src/` |
| SonarQube | Code quality | Integración externa |
| pytest-cov | Coverage | `pytest --cov=src` |
