from __future__ import annotations


def _scope(category: str | None, product_id: int | None) -> tuple[str, str]:
    if product_id is not None:
        return "product", str(product_id)
    if category:
        return "category", category
    return "all", ""


def filters(conn) -> dict:
    cats = conn.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()
    products = conn.execute(
        "SELECT id, name, category FROM products ORDER BY category, name"
    ).fetchall()
    return {
        "categories": [r["category"] for r in cats],
        "products": list(products),
    }


def kpis(conn) -> dict:
    row = conn.execute(
        """
        WITH bounds AS (
            SELECT MAX(date) AS max_d FROM sales
        ),
        cur AS (
            SELECT
                COALESCE(SUM(revenue), 0) AS ventas,
                COALESCE(SUM(qty), 0) AS unidades,
                CASE WHEN COUNT(*) = 0 THEN 0
                     ELSE SUM(revenue) / COUNT(*)
                END AS ticket
            FROM sales, bounds
            WHERE date > bounds.max_d - 365
        ),
        prev AS (
            SELECT COALESCE(SUM(revenue), 0) AS ventas
            FROM sales, bounds
            WHERE date <= bounds.max_d - 365
              AND date > bounds.max_d - 730
        )
        SELECT
            cur.ventas::float AS ventas_totales,
            cur.unidades::float AS unidades_totales,
            CASE WHEN prev.ventas = 0 THEN NULL
                 ELSE ((cur.ventas - prev.ventas) / prev.ventas)::float
            END AS yoy,
            cur.ticket::float AS ticket_promedio
        FROM cur, prev
        """
    ).fetchone()
    return row or {"ventas_totales": 0, "unidades_totales": 0, "yoy": None, "ticket_promedio": 0}


def trend(conn, category=None, product_id=None) -> list[dict]:
    scope, key = _scope(category, product_id)
    rows = conn.execute(
        """
        SELECT
            date::text AS date,
            y_true::float AS y_true,
            y_pred::float AS y_pred,
            y_true_qty::float AS y_true_qty,
            y_pred_qty::float AS y_pred_qty
        FROM predictions
        WHERE horizon = 0 AND scope = %s AND scope_key = %s
        ORDER BY date
        """,
        (scope, key),
    ).fetchall()
    return list(rows)


def forecast(conn, horizon: int, category=None, product_id=None) -> list[dict]:
    scope, key = _scope(category, product_id)
    rows = conn.execute(
        """
        SELECT
            date::text AS date,
            y_pred::float AS y_pred,
            y_pred_qty::float AS y_pred_qty,
            horizon
        FROM predictions
        WHERE horizon = %s AND scope = %s AND scope_key = %s
        ORDER BY date
        """,
        (horizon, scope, key),
    ).fetchall()
    return list(rows)


def by_category(conn) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            p.category,
            SUM(s.revenue)::float AS revenue,
            SUM(s.qty)::int AS qty
        FROM sales s
        JOIN products p ON p.id = s.product_id
        GROUP BY p.category
        ORDER BY revenue DESC
        """
    ).fetchall()
    return list(rows)


def by_product(conn, category: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            p.id,
            p.name,
            p.category,
            SUM(s.revenue)::float AS revenue,
            SUM(s.qty)::int AS qty,
            COALESCE(SUM(s.qty) FILTER (WHERE s.promo), 0)::int AS promo_qty,
            COALESCE(SUM(s.revenue) FILTER (WHERE s.promo), 0)::float AS promo_revenue
        FROM sales s
        JOIN products p ON p.id = s.product_id
        WHERE p.category = %s
        GROUP BY p.id, p.name, p.category
        ORDER BY revenue DESC
        """,
        (category,),
    ).fetchall()
    return list(rows)


def by_region(conn) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            st.id,
            st.name,
            st.region,
            st.lat::float AS lat,
            st.lon::float AS lon,
            SUM(s.revenue)::float AS revenue,
            SUM(s.qty)::int AS qty
        FROM sales s
        JOIN stores st ON st.id = s.store_id
        GROUP BY st.id, st.name, st.region, st.lat, st.lon
        ORDER BY revenue DESC
        """
    ).fetchall()
    return list(rows)


def promos_impact(conn) -> dict:
    daily = conn.execute(
        """
        WITH daily AS (
            SELECT
                date,
                BOOL_OR(promo) AS has_promo,
                SUM(revenue)::float AS revenue
            FROM sales
            GROUP BY date
        )
        SELECT
            has_promo,
            AVG(revenue)::float AS avg_revenue,
            COUNT(*)::int AS n_days,
            SUM(revenue)::float AS total_revenue
        FROM daily
        GROUP BY has_promo
        """
    ).fetchall()
    with_p = next((r for r in daily if r["has_promo"]), None)
    without = next((r for r in daily if not r["has_promo"]), None)
    avg_yes = with_p["avg_revenue"] if with_p else 0.0
    avg_no = without["avg_revenue"] if without else 0.0
    lift = None if not avg_no else (avg_yes / avg_no) - 1.0
    return {
        "con_promocion": with_p,
        "sin_promocion": without,
        "lift": lift,
    }


def model_metrics(conn, category=None, product_id=None, target="revenue"):
    scope, key = _scope(category, product_id)
    tgt = "qty" if target == "qty" else "revenue"
    return conn.execute(
        """
        SELECT
            trained_at::text AS trained_at,
            scope,
            scope_key,
            target,
            r2::float AS r2,
            mae::float AS mae,
            mape::float AS mape,
            n_train,
            n_test
        FROM model_metrics
        WHERE scope = %s AND scope_key = %s AND target = %s
        ORDER BY trained_at DESC
        LIMIT 1
        """,
        (scope, key, tgt),
    ).fetchone()
