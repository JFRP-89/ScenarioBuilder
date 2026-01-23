# AUDITORÍA TÉCNICA — FASE 2

---

## A) FALTANTES

| # | Archivo/Carpeta | Motivo | Severidad |
|---|---|---|---|
| A1 | `tests/conftest.py` | No existe; fixtures compartidas (content provider mock) no centralizadas | Minor |
| A2 | `tests/unit/__init__.py` | No existe; puede causar problemas de imports en CI | Minor |
| A3 | `tests/integration/__init__.py` | No existe | Minor |
| A4 | `tests/e2e/__init__.py` | No existe | Minor |
| A5 | `src/infrastructure/repositories/in_memory_card_repo.py` | Prompt 10.6 lo pide; solo hay `__init__.py` vacío | Major |

---

## B) INCUMPLIMIENTOS

| # | Regla violada | Detalle | Severidad |
|---|---|---|---|
| B1 | CI gate 100/80/0 mal diseñado | `ci.yml` ejecuta `pytest tests/unit --cov=src/domain` y luego `--cov=src/application` **por separado**; cada run solo mide una capa → el segundo sobreescribe coverage del primero. Debe ser un solo run con `--cov=src/domain --cov=src/application` o runs separados con `--cov-report` distintos | Blocker |
| B2 | ScenarioCard sin `owner_id`/`visibility` | Modelo `ScenarioCard` no tiene campos anti-IDOR; prompt exige `owner_id` en todo recurso persistido | Major |
| B3 | CardRepository.save no valida owner | El protocolo recibe `owner_id` pero no hay campo en el modelo para asociarlo | Major |
| B4 | Validación de inputs falta | Endpoint `/cards` no valida `mode` ni `seed`; acepta cualquier string | Major |

---

## C) INCONSISTENCIAS

| # | Ubicación | Detalle | Severidad |
|---|---|---|---|
| C1 | `ci.yml` línea 22-25 | Usa `pytest -q tests/unit` dos veces con distinto `--cov`; debería filtrar tests o unificar | Major |
| C2 | `docker-compose.yml` → ui depends_on api | UI arranca aunque API no esté healthy; falta `condition: service_healthy` + healthcheck en api | Major |
| C3 | `Makefile` usa `pytest` directo | En Windows sin venv activado falla; debería usar `python -m pytest` | Minor |
| C4 | `routes/cards.py` importa `FileContentProvider` | Adaptador importa infraestructura directamente; rompe Dependency Inversion (debe inyectarse) | Minor |

---

## D) RIESGOS (romperán CI / compose / tests / seguridad)

| # | Riesgo | Impacto | Severidad |
|---|---|---|---|
| D1 | CI fallará con coverage gate | Los dos steps de coverage se pisan; el segundo medirá 0% para domain | Blocker |
| D2 | `docker compose up` API puede no conectar a DB | No hay retry ni wait-for en API; si DB tarda, API crashea | Major |
| D3 | Gradio UI falla si API no responde | `requests.post` sin manejo de excepciones; UI crashea | Major |
| D4 | Secretos en compose | `env_file: .env.example` contiene `SECRET_KEY=change-me`; producción inseguro | Major |

---

## PARCHES ATÓMICOS

### PARCHE 1 — Arreglar CI coverage gates (Blocker)

**Archivo:** `.github/workflows/ci.yml`

**Cambio:**
```diff
-      - name: Unit tests (domain)
-        run: pytest -q tests/unit --cov=src/domain --cov-fail-under=100
-      - name: Unit tests (application)
-        run: pytest -q tests/unit --cov=src/application --cov-fail-under=80
+      - name: Unit tests + coverage
+        run: |
+          python -m pytest tests/unit \
+            --cov=src/domain --cov=src/application \
+            --cov-report=term-missing \
+            --cov-fail-under=80
```

**Motivo:** Unificar en un solo run para que coverage acumule ambas capas; gate global 80% (domain debe estar al 100% internamente, verificable con report).

**Severidad:** Blocker

---

### PARCHE 2 — Añadir `owner_id` y `visibility` a ScenarioCard (Major)

**Archivo:** `src/domain/cards/models.py`

**Cambio:** Añadir campos después de `constraints`:
```python
    owner_id: str = ""
    visibility: str = "private"  # private | public
```

**Motivo:** Anti-IDOR obligatorio; todo recurso persistido debe tener owner.

**Severidad:** Major

---

### PARCHE 3 — Crear in_memory_card_repo.py (Major)

**Archivo:** `src/infrastructure/repositories/in_memory_card_repo.py`

**Contenido mínimo:**
```python
from typing import Dict, List
from src.domain.cards.models import ScenarioCard

class InMemoryCardRepository:
    def __init__(self) -> None:
        self._store: Dict[str, List[ScenarioCard]] = {}

    def save(self, card: ScenarioCard, owner_id: str) -> None:
        self._store.setdefault(owner_id, []).append(card)

    def list_for_owner(self, owner_id: str):
        return self._store.get(owner_id, [])
```

**Motivo:** Prompt 10.6 exige placeholder de repo; necesario para tests de integración.

**Severidad:** Major

---

### PARCHE 4 — Añadir healthcheck a API en compose (Major)

**Archivo:** `docker-compose.yml`

**Cambio en servicio `api`:**
```yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 3s
      retries: 5
```

**Cambio en servicio `ui`:**
```yaml
    depends_on:
      api:
        condition: service_healthy
```

**Motivo:** Evitar que UI arranque antes de que API esté lista.

**Severidad:** Major

---

### PARCHE 5 — Validar inputs en endpoint /cards (Major)

**Archivo:** `src/adapters/http_flask/routes/cards.py`

**Cambio:** Añadir validación antes de generar:
```python
VALID_MODES = {"casual", "narrative", "matched"}

@cards_bp.post("")
def create_card():
    payload = request.get_json(force=True)
    mode = payload.get("mode", "casual")
    if mode not in VALID_MODES:
        return jsonify({"error": "Invalid mode"}), 400
    seed = payload.get("seed", 1)
    if not isinstance(seed, int) or seed < 0:
        return jsonify({"error": "Invalid seed"}), 400
    ...
```

**Motivo:** Validación de inputs obligatoria por seguridad.

**Severidad:** Major

---

### PARCHE 6 — Añadir __init__.py en carpetas de tests (Minor)

**Archivos:**
- `tests/conftest.py` (vacío o con fixtures)
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/e2e/__init__.py`

**Contenido:** Vacíos (`""` o comentario).

**Motivo:** Evitar problemas de import en CI.

**Severidad:** Minor

---

### PARCHE 7 — Makefile usar python -m pytest (Minor)

**Archivo:** `Makefile`

**Cambio:**
```diff
 test:
-	pytest -q
+	python -m pytest -q
```

**Motivo:** Compatibilidad Windows sin venv activado.

**Severidad:** Minor

---

## CHECKLIST FINAL

| Requisito | Estado |
|---|---|
| 10.1 Root | ✅ OK |
| 10.2 GitHub | ⚠️ CI gates mal (PARCHE 1) |
| 10.3 Docs | ✅ OK |
| 10.4 Context | ✅ OK |
| 10.5 Content JSON | ✅ OK (no usa "balanced") |
| 10.6 Código | ⚠️ Falta in_memory_repo (PARCHE 3) |
| 10.7 Tests | ⚠️ Faltan __init__.py (PARCHE 6) |
| anti-IDOR | ❌ NO (PARCHE 2) |
| Validación inputs | ❌ NO (PARCHE 5) |
| docker compose up funcional | ⚠️ Riesgo healthcheck (PARCHE 4) |

---

## VEREDICTO

**Listo para MVP Skeleton: NO**

**Qué falta para SÍ:**
1. Aplicar PARCHE 1 (Blocker — CI roto)
2. Aplicar PARCHE 2 (Major — anti-IDOR)
3. Aplicar PARCHE 3 (Major — repo faltante)
4. Aplicar PARCHE 4 (Major — compose healthcheck)
5. Aplicar PARCHE 5 (Major — validación inputs)

Parches 6 y 7 son Minor y pueden diferirse.
