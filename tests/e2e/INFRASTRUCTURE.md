# E2E Infrastructure Checklist

## ✅ Archivos creados

### Core Infrastructure
- ✅ `tests/e2e/conftest.py` - Fixtures principales (docker-compose, browser, page)
- ✅ `tests/e2e/utils.py` - Helpers (wait_http_ok, dump_debug_artifacts)
- ✅ `tests/e2e/artifacts/` - Directorio para HTML + screenshots (gitignored)
- ✅ `tests/e2e/README.md` - Documentación completa de uso

### Test Files
- ✅ `tests/e2e/test_e2e_placeholder.py` - Smoke test con `@pytest.mark.e2e`

### Configuration
- ✅ `pytest.ini` - Marker `e2e` registrado
- ✅ `.gitignore` - Artifacts excluidos (html, png, jpg)
- ✅ `requirements.txt` - Ya tiene `playwright==1.49.0` y `requests==2.32.3`
- ✅ Playwright browsers - Chromium instalado

## 📋 Fixtures disponibles en conftest.py

### Session-scoped
- **`e2e_base_urls`**: Dict con `{"api": "http://localhost:8000", "ui": "http://localhost:7860"}`
- **`docker_compose_up`**: Levanta docker-compose, espera health checks, teardown al final
- **`playwright_instance`**: Playwright sync API instance
- **`browser`**: Chromium browser (reutilizado por todos los tests)

### Function-scoped
- **`page`**: Nueva Page por cada test (auto-cleanup)

## 🛠️ Helpers en utils.py

- **`wait_http_ok(url, timeout_s, interval_s, acceptable_codes)`**: Polling HTTP
- **`dump_debug_artifacts(page, name)`**: Guarda HTML + screenshot en `artifacts/`

## 🚀 Verificación

### 1. Smoke test (sin docker)
```bash
pytest -q tests/e2e/test_e2e_placeholder.py -k "not docker" --co
```

### 2. Test completo con docker-compose
```bash
pytest -v tests/e2e -m e2e
```

## 🐳 Docker Compose Lifecycle

La fixture `docker_compose_up` (scope=session):
1. **Setup**: `docker compose up -d --build api ui`
2. **Health Check**: Polling hasta 120s:
   - API: `GET http://localhost:8000/health` → 200
   - UI: `GET http://localhost:7860/` → 200 o 302
3. **Teardown**: `docker compose down -v`

Si falla, imprime:
- `docker compose ps`
- `docker compose logs --tail=200 api ui`

## 📁 Artifacts

Directorio: `tests/e2e/artifacts/`
- Creado automáticamente por `dump_debug_artifacts()`
- Gitignored: `*.html`, `*.png`, `*.jpg`
- Incluye `.gitkeep` para rastrear directorio vacío

## 🎯 Próximos pasos

1. Implementar tests reales en `tests/e2e/test_gradio_ui.py`:
   - Flujo completo de generación de carta
   - Validaciones de inputs
   - Modos de juego (casual, narrative, matched)
   - Seed determinista
   - Error handling

2. Implementar tests API en `tests/e2e/test_api_endpoints.py`:
   - POST /cards/scenario
   - GET /cards/{card_id}
   - Error responses (4xx, 5xx)

3. CI/CD integration:
   - Job separado para E2E tests
   - Usar docker-compose en GitHub Actions
   - Subir artifacts en failures

## ⚠️ Restricciones respetadas

✅ Solo archivos creados/editados en `tests/e2e/**`
✅ NO se tocó nada bajo `src/`
✅ NO se modificaron tests unit/integration existentes
✅ Marker `@pytest.mark.e2e` aplicado
✅ Docker compose y health checks robustos con debug output
