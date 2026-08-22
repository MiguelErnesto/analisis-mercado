# Dashboard de ventas con ML

Stack: PostgreSQL propio → Pandas / Scikit-learn → FastAPI → D3.js.

**Restricción:** no instales Python ni Postgres en el host. Solo Docker.

Este Compose levanta **su propio** Postgres (`analisis-mercado-db`, imagen local `postgres:16-alpine`). No usa ni modifica `planificador-postgres`. El puerto 5432 no se publica al host.

## Requisitos

- Docker y Docker Compose

## Configuración

Copia [`.env.example`](.env.example) a `.env` si no existe:

| Variable | Qué es |
|---|---|
| `POSTGRES_HOST` | Servicio Compose (`db`) |
| `POSTGRES_PORT` | `5432` (interno) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | Credenciales de este stack |
| `POSTGRES_DB` | `analisis_mercado` |
| `POSTGRES_ADMIN_DB` | `postgres` (para `CREATE DATABASE` si hace falta) |

## Arranque

```bash
DOCKER_SCAN_SUGGEST=false docker compose build
docker compose up -d db
docker compose run --rm etl
docker compose up -d api
```

- ETL: schema, datos sintéticos (24 meses), RandomForest, pronósticos 7/15/30. **Borra y regenera** las tablas.
- API + dashboard: [http://localhost:8000](http://localhost:8000)

Si ya restauraste un dump, no hace falta el ETL: `docker compose up -d`.

Re-entrenar:

```bash
docker compose run --rm etl
```

Parar este stack (no toca otros proyectos):

```bash
docker compose stop
```

## Pantallas

- **/** — KPIs (ventas 12 meses, YoY, ticket medio), real vs predicho, forecast 7/15/30, R²/MAE/MAPE
- **/analisis** — categorías, mapa de tiendas, lift de promociones

## API

- `GET /api/kpis`
- `GET /api/sales/trend`
- `GET /api/forecast?horizon=7|15|30`
- `GET /api/sales/by-category`
- `GET /api/sales/by-region`
- `GET /api/promos/impact`
- `GET /api/model/metrics`
