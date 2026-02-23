# Runbook de Deploy

## Prerequisitos

- Docker 24+ y Docker Compose v2
- Archivo `.env` configurado (ver sección de variables)
- Acceso al registro de imágenes (si se usa CI/CD)
- Puerto 8000 disponible (app) y 5432 (PostgreSQL, solo si se expone)

---

## Variables de entorno

Copiar `.env.example` a `.env` y configurar:

| Variable | Requerida | Descripción | Ejemplo |
|----------|-----------|-------------|---------|
| `DATABASE_URL` | ✅ Producción | URL de conexión PostgreSQL | `postgresql://user:pass@db:5432/scenariobuilder` |
| `DATABASE_URL_TEST` | Solo tests | URL de BD de tests | `postgresql://user:pass@localhost:5432/test_sb` |
| `POSTGRES_DB` | ✅ Docker | Nombre de la BD | `scenariobuilder` |
| `POSTGRES_USER` | ✅ Docker | Usuario PostgreSQL | `sb_user` |
| `POSTGRES_PASSWORD` | ✅ Docker | Contraseña (nunca en repo) | `<secreto>` |
| `POSTGRES_PORT` | Opcional | Puerto PostgreSQL (default: 5432) | `5432` |
| `HOST` | Opcional | Host de bind (default: 0.0.0.0) | `0.0.0.0` |
| `PORT` | Opcional | Puerto de la app (default: 8000) | `8000` |
| `APP_ENV` | Opcional | `prod` o `dev` (afecta fallbacks) | `prod` |

**Regla de seguridad**: `.env` está en `.gitignore`. Nunca commitear secretos.

---

## Deploy con Docker Compose

### 1. Configurar entorno

```bash
cp .env.example .env
# Editar .env con credenciales reales
```

### 2. Construir y levantar

```bash
docker compose up --build -d
```

Esto levanta:
- **db**: PostgreSQL 16 (Alpine) con volumen persistente `scenariobuilder-pgdata`
- **app**: Python 3.11-slim con Uvicorn (Flask API + Gradio UI)

### 3. Verificar salud

```bash
# App
curl -s http://localhost:8000/health
# → {"status": "healthy", "timestamp": "..."}

# Base de datos (desde dentro del contenedor)
docker compose exec db pg_isready -U $POSTGRES_USER
# → accepting connections
```

### 4. Verificar migraciones

Las migraciones de Alembic se ejecutan **automáticamente** al iniciar el contenedor
(`alembic upgrade head` en el CMD del Dockerfile).

```bash
# Ver estado de migraciones
docker compose exec app alembic current
# → <revision> (head)

# Ver historial
docker compose exec app alembic history
```

### 5. Verificar accesos

| URL | Servicio |
|-----|----------|
| `http://localhost:8000/sb/` | Gradio UI |
| `http://localhost:8000/auth/login` | API autenticación |
| `http://localhost:8000/cards` | API cards |
| `http://localhost:8000/health` | Health check |

---

## Arquitectura del stack

```
┌─────────────────────────────────────────┐
│                 NGINX                    │  (futuro — reverse proxy)
├─────────────────────────────────────────┤
│           app (puerto 8000)             │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │ Flask API    │  │ Gradio UI        │  │
│  │ /auth/*      │  │ /sb/*            │  │
│  │ /cards/*     │  │                  │  │
│  │ /favorites/* │  │                  │  │
│  │ /health      │  │                  │  │
│  └─────────────┘  └──────────────────┘  │
│            Uvicorn (ASGI)               │
├─────────────────────────────────────────┤
│           db (PostgreSQL 16)            │
│    Tablas: cards, users, sessions,      │
│            favorites                    │
│    Volumen: scenariobuilder-pgdata      │
└─────────────────────────────────────────┘
```

---

## Rollback

### Rollback completo

```bash
docker compose down
# Los datos persisten en el volumen
docker compose up -d
```

### Rollback de migración

```bash
docker compose exec app alembic downgrade -1
# Volver al estado anterior
```

### Rollback destructivo (reset total)

```bash
docker compose down -v   # ⚠️ Elimina volúmenes (datos)
docker compose up --build -d
```

---

## Monitorización

### Health check

El contenedor tiene health check configurado internamente:

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

### Logs

```bash
# Todos los servicios
docker compose logs -f

# Solo la app
docker compose logs -f app

# Solo la base de datos
docker compose logs -f db

# Últimas 100 líneas
docker compose logs --tail=100 app
```

### Recursos

Límites configurados en `docker-compose.yml`:

| Servicio | CPU | Memoria |
|----------|-----|---------|
| app | 1 core | 1 GB |
| db | 1 core | 1 GB |

---

## Dockerfile — Estructura multi-stage

```dockerfile
# Stage 1: base
FROM python:3.11-slim AS base
# PYTHONPATH=/app/src, instala curl para healthcheck

# Stage 2: deps
FROM base AS deps
# Instala requirements.txt (cacheado en layer)

# Stage 3: final
FROM deps AS final
# Copia src/, content/, alembic/
# Usuario no-root: appuser (UID 1000)
# Expone puerto 8000
# CMD: alembic upgrade head && uvicorn
```

**Seguridad del contenedor:**
- Usuario no-root (`appuser`, UID 1000)
- Imagen base slim (mínima superficie de ataque)
- Sin herramientas de desarrollo en producción
- Health check via curl

---

## Troubleshooting

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| App no arranca | `DATABASE_URL` mal configurada | Verificar `.env`, `docker compose logs app` |
| Migraciones fallan | BD no disponible aún | Verificar `depends_on` y health de `db` |
| Puerto ocupado | Otro servicio en 8000/5432 | Cambiar `PORT`/`POSTGRES_PORT` en `.env` |
| Health check falla | App aún iniciando | Esperar `start_period` (15s); ver logs |
| Datos perdidos tras restart | Se usó `down -v` | Los volúmenes se eliminan con `-v` |
| Permisos en Linux | UID mismatch | Verificar que el volumen sea accesible por UID 1000 |

---

## Deploy manual (sin Docker)

Para desarrollo o entornos sin Docker:

```bash
# 1. Configurar entorno
python -3.11 -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt

# 2. Configurar BD (opcional — sin DB usa in-memory)
export DATABASE_URL=postgresql://user:pass@localhost:5432/scenariobuilder
alembic upgrade head

# 3. Ejecutar
PYTHONPATH=src python -c "
import uvicorn
from adapters.combined_app import create_combined_app
uvicorn.run(create_combined_app(), host='127.0.0.1', port=8000)
"
```

### PowerShell (Windows)

```powershell
$env:PYTHONPATH = "src"
python -c "import uvicorn; from adapters.combined_app import create_combined_app; uvicorn.run(create_combined_app(), host='127.0.0.1', port=8000)"
```
