from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.db import get_conn
from api import queries

app = FastAPI(title="Dashboard ventas ML")


def _product_id(raw: Optional[str]) -> Optional[int]:
    if raw is None or raw == "":
        return None
    return int(raw)


@app.get("/api/kpis")
def api_kpis():
    with get_conn() as conn:
        return queries.kpis(conn)


@app.get("/api/filters")
def api_filters():
    with get_conn() as conn:
        return queries.filters(conn)


@app.get("/api/sales/trend")
def api_trend(
    category: Optional[str] = None,
    product_id: Optional[str] = None,
):
    with get_conn() as conn:
        return queries.trend(conn, category or None, _product_id(product_id))


@app.get("/api/forecast")
def api_forecast(
    horizon: int = Query(7, description="7, 15 o 30"),
    category: Optional[str] = None,
    product_id: Optional[str] = None,
):
    if horizon not in (7, 15, 30):
        raise HTTPException(400, "horizon debe ser 7, 15 o 30")
    with get_conn() as conn:
        return queries.forecast(conn, horizon, category or None, _product_id(product_id))


@app.get("/api/sales/by-category")
def api_category():
    with get_conn() as conn:
        return queries.by_category(conn)


@app.get("/api/sales/by-product")
def api_product(category: str = Query(..., min_length=1)):
    with get_conn() as conn:
        return queries.by_product(conn, category)


@app.get("/api/sales/by-region")
def api_region():
    with get_conn() as conn:
        return queries.by_region(conn)


@app.get("/api/promos/impact")
def api_promos():
    with get_conn() as conn:
        return queries.promos_impact(conn)


@app.get("/api/model/metrics")
def api_metrics(
    category: Optional[str] = None,
    product_id: Optional[str] = None,
    target: str = Query("revenue"),
):
    if target not in ("revenue", "qty"):
        raise HTTPException(400, "target debe ser revenue o qty")
    with get_conn() as conn:
        row = queries.model_metrics(conn, category or None, _product_id(product_id), target)
        if not row:
            raise HTTPException(404, "Sin métricas: ejecuta el ETL")
        return row


@app.get("/")
def index():
    return FileResponse("frontend/index.html")


@app.get("/analisis")
def analisis():
    return FileResponse("frontend/analisis.html")


app.mount("/static", StaticFiles(directory="frontend"), name="static")
