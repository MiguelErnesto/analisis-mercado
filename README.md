# Dashboard de ventas con ML

Stack: PostgreSQL (contenedor existente) → Pandas / Scikit-learn → FastAPI → D3.js.

**Restricción:** no instales Python ni Postgres en el host. Solo Docker.

## Requisitos

- Docker y Docker Compose
- Un PostgreSQL ya levantado en Docker (en esta máquina: `planificador-postgres`)

## Conectar al Postgres existente

1. Nombre del contenedor y su red:

```bash
docker ps --format '{{.Names}} {{.Image}}'
docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' NOMBRE_CONTENEDOR_POSTGRES
```

2. Copia [`.env.example`](.env.example) a `.env` y rellena:

| Variable | Qué es |
|---|---|
| `POSTGRES_DOCKER_NETWORK` | Red del contenedor Postgres |
| `POSTGRES_HOST` | Nombre del contenedor (DNS interno, no `localhost`) |
| `POSTGRES_PORT` | Casi siempre `5432` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | Credenciales existentes |
| `POSTGRES_DB` | `analisis_mercado` (el ETL la crea; no toca otras bases) |
| `POSTGRES_ADMIN_DB` | Base a la que conectar para `CREATE DATABASE` |

Valores por defecto de este entorno:

- red `planificador-eventos_default`
- host `planificador-postgres`
- usuario/clave `planificador`

## Arranque

```bash
DOCKER_SCAN_SUGGEST=false docker compose build
docker compose run --rm etl
docker compose up api
```

`docker scan` no es un error: es un aviso de Snyk tras un build correcto.

- ETL: schema, datos sintéticos (24 meses), RandomForest, pronósticos 7/15/30.
- API + dashboard: [http://localhost:8000](http://localhost:8000)

Re-entrenar:

```bash
docker compose run --rm etl
```

Parar el dashboard: `docker compose stop api`

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
