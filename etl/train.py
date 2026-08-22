from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
import psycopg
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score

from etl.dbconfig import pg_kwargs
from etl.features import FEATURE_COLS, add_features, daily_sales, train_ready


def _read_frames(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.date, s.revenue, s.qty, s.promo, s.product_id, p.category
            FROM sales s
            JOIN products p ON p.id = s.product_id
            """
        )
        sales = pd.DataFrame(
            cur.fetchall(),
            columns=["date", "revenue", "qty", "promo", "product_id", "category"],
        )
        sales["date"] = pd.to_datetime(sales["date"])
        sales["revenue"] = sales["revenue"].astype(float)
        sales["qty"] = sales["qty"].astype(float)
        cur.execute("SELECT id, name, category FROM products ORDER BY category, name")
        products = pd.DataFrame(cur.fetchall(), columns=["id", "name", "category"])
        cur.execute("SELECT date FROM holidays")
        holidays = pd.to_datetime(pd.Series([r[0] for r in cur.fetchall()], name="date"))
    return sales, products, holidays


def _complete_daily(slice_df, start, end):
    daily = daily_sales(slice_df[["date", "revenue", "qty", "promo"]])
    idx = pd.date_range(start, end, freq="D")
    daily = daily.set_index("date").reindex(idx)
    daily.index.name = "date"
    daily["revenue"] = daily["revenue"].fillna(0)
    daily["qty"] = daily["qty"].fillna(0)
    daily["promo_rate"] = daily["promo_rate"].fillna(0)
    return daily.reset_index()


def _fit_target(daily, holidays, value_col, n_estimators):
    feat = train_ready(daily, holidays, value_col)
    if len(feat) < 90:
        return None, None, None
    train = feat.iloc[:-60]
    test = feat.iloc[-60:]
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    y_train = train[value_col].to_numpy(dtype=float)
    model.fit(train[FEATURE_COLS].to_numpy(dtype=float), y_train)
    y_hat = model.predict(test[FEATURE_COLS].to_numpy(dtype=float))
    y_test = np.maximum(test[value_col].to_numpy(dtype=float), 1e-6)
    metrics = {
        "target": value_col if value_col != "revenue" else "revenue",
        "r2": float(r2_score(test[value_col], y_hat)),
        "mae": float(mean_absolute_error(test[value_col], y_hat)),
        "mape": float(mean_absolute_percentage_error(y_test, y_hat)),
        "n_train": len(train),
        "n_test": len(test),
    }
    hist = pd.DataFrame(
        {
            "date": feat["date"].dt.date,
            "y_true": feat[value_col].to_numpy(dtype=float),
            "y_pred": model.predict(feat[FEATURE_COLS].to_numpy(dtype=float)),
        }
    )
    return model, hist, metrics


def _recursive_forecast(model, daily, holidays, horizon, value_col):
    hist = daily.copy().sort_values("date").reset_index(drop=True)
    last = hist["date"].max()
    dow_promo = hist.groupby(hist["date"].dt.dayofweek)["promo_rate"].mean()
    rows = []
    for step in range(1, horizon + 1):
        d = last + timedelta(days=step)
        promo_rate = float(dow_promo.get(d.dayofweek, hist["promo_rate"].mean()))
        nxt = {col: [np.nan] for col in hist.columns if col != "date"}
        nxt["date"] = [pd.Timestamp(d)]
        nxt["promo_rate"] = [promo_rate]
        tmp = pd.concat([hist, pd.DataFrame(nxt)], ignore_index=True)
        feat = add_features(tmp, holidays, value_col).iloc[-1]
        x = feat[FEATURE_COLS].to_numpy(dtype=float).reshape(1, -1)
        yhat = float(model.predict(x)[0])
        row = {col: hist.iloc[-1][col] if col not in ("date", value_col, "promo_rate") else np.nan for col in hist.columns}
        row["date"] = pd.Timestamp(d)
        row[value_col] = yhat
        row["promo_rate"] = promo_rate
        hist = pd.concat([hist, pd.DataFrame([row])], ignore_index=True)
        rows.append(
            {
                "date": d.date() if hasattr(d, "date") else d,
                "y_pred": max(yhat, 0.0),
                "horizon": horizon,
            }
        )
    return pd.DataFrame(rows)


def _fit_series(daily, holidays, scope, scope_key, n_estimators=100):
    model_r, hist_r, met_r = _fit_target(daily, holidays, "revenue", n_estimators)
    model_q, hist_q, met_q = _fit_target(daily, holidays, "qty", max(40, n_estimators // 2))
    if model_r is None or model_q is None:
        print(f"  skip {scope}/{scope_key}: serie corta")
        return None, None
    hist = hist_r.rename(columns={"y_true": "y_true", "y_pred": "y_pred"}).merge(
        hist_q.rename(columns={"y_true": "y_true_qty", "y_pred": "y_pred_qty"}),
        on="date",
    )
    hist["horizon"] = 0
    hist["scope"] = scope
    hist["scope_key"] = scope_key
    future_parts = []
    for h in (7, 15, 30):
        fr = _recursive_forecast(model_r, daily, holidays, h, "revenue")
        fq = _recursive_forecast(model_q, daily, holidays, h, "qty")
        f = fr.merge(fq, on=["date", "horizon"], suffixes=("", "_qty"))
        f = f.rename(columns={"y_pred": "y_pred", "y_pred_qty": "y_pred_qty"})
        f["y_true"] = None
        f["y_true_qty"] = None
        f["scope"] = scope
        f["scope_key"] = scope_key
        future_parts.append(f)
    pred = pd.concat([hist, *future_parts], ignore_index=True)
    met_r = dict(met_r, scope=scope, scope_key=scope_key, target="revenue")
    met_q = dict(met_q, scope=scope, scope_key=scope_key, target="qty")
    return pred, [met_r, met_q]


def train_and_forecast() -> None:
    with psycopg.connect(**pg_kwargs()) as conn:
        sales, products, holidays = _read_frames(conn)
        start, end = sales["date"].min(), sales["date"].max()
        jobs = [("all", "", sales, 80)]
        for cat in sorted(products["category"].unique()):
            jobs.append(("category", cat, sales[sales["category"] == cat], 60))
        for row in products.itertuples(index=False):
            jobs.append(("product", str(row.id), sales[sales["product_id"] == row.id], 40))

        all_pred = []
        all_metrics = []
        for scope, key, slc, trees in jobs:
            label = key or "total"
            print(f"Entrenando {scope}/{label} ({len(slc):,} líneas)...")
            daily = _complete_daily(slc, start, end)
            pred, metrics = _fit_series(daily, holidays, scope, key, n_estimators=trees)
            if pred is None:
                continue
            all_pred.append(pred)
            all_metrics.extend(metrics)
            rev = metrics[0]
            qty = metrics[1]
            print(
                f"  $ R²={rev['r2']:.3f}  und R²={qty['r2']:.3f}  "
                f"MAPE $={rev['mape']:.3f} und={qty['mape']:.3f}"
            )

        pred = pd.concat(all_pred, ignore_index=True)
        cols = [
            "date",
            "y_true",
            "y_pred",
            "y_true_qty",
            "y_pred_qty",
            "horizon",
            "scope",
            "scope_key",
        ]
        pred = pred[cols]
        conn.execute("TRUNCATE predictions, model_metrics")
        with conn.cursor() as cur:
            with cur.copy(
                "COPY predictions (date, y_true, y_pred, y_true_qty, y_pred_qty, horizon, scope, scope_key) FROM STDIN"
            ) as copy:
                for row in pred.itertuples(index=False, name=None):
                    dt, y_true, y_pred, y_true_q, y_pred_q, hz, scope, skey = row
                    if y_true is not None and pd.isna(y_true):
                        y_true = None
                    if y_true_q is not None and pd.isna(y_true_q):
                        y_true_q = None
                    copy.write_row(
                        (
                            dt,
                            y_true,
                            float(y_pred),
                            y_true_q,
                            float(y_pred_q),
                            int(hz),
                            scope,
                            skey,
                        )
                    )
            for m in all_metrics:
                cur.execute(
                    """
                    INSERT INTO model_metrics
                      (scope, scope_key, target, r2, mae, mape, n_train, n_test)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        m["scope"],
                        m["scope_key"],
                        m["target"],
                        m["r2"],
                        m["mae"],
                        m["mape"],
                        m["n_train"],
                        m["n_test"],
                    ),
                )
        conn.commit()
        print(f"Listos {len(all_metrics)} modelos")
