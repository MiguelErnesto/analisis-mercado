DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS model_metrics CASCADE;
DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS holidays CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS stores CASCADE;

CREATE TABLE stores (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    lat  DOUBLE PRECISION NOT NULL,
    lon  DOUBLE PRECISION NOT NULL
);

CREATE TABLE products (
    id       INTEGER PRIMARY KEY,
    name     TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE holidays (
    date DATE PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE sales (
    id         BIGSERIAL PRIMARY KEY,
    date       DATE NOT NULL,
    store_id   INTEGER NOT NULL REFERENCES stores (id),
    product_id INTEGER NOT NULL REFERENCES products (id),
    qty        INTEGER NOT NULL,
    revenue    NUMERIC(12, 2) NOT NULL,
    promo      BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_sales_date ON sales (date);
CREATE INDEX idx_sales_store ON sales (store_id);
CREATE INDEX idx_sales_product ON sales (product_id);
CREATE INDEX idx_sales_promo ON sales (promo);

CREATE TABLE predictions (
    date         DATE NOT NULL,
    y_true       DOUBLE PRECISION,
    y_pred       DOUBLE PRECISION NOT NULL,
    y_true_qty   DOUBLE PRECISION,
    y_pred_qty   DOUBLE PRECISION NOT NULL DEFAULT 0,
    horizon      INTEGER NOT NULL DEFAULT 0,
    scope        TEXT NOT NULL DEFAULT 'all',
    scope_key    TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (date, horizon, scope, scope_key)
);

CREATE TABLE model_metrics (
    id         SERIAL PRIMARY KEY,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scope      TEXT NOT NULL DEFAULT 'all',
    scope_key  TEXT NOT NULL DEFAULT '',
    target     TEXT NOT NULL DEFAULT 'revenue',
    r2         DOUBLE PRECISION,
    mae        DOUBLE PRECISION,
    mape       DOUBLE PRECISION,
    n_train    INTEGER,
    n_test     INTEGER
);
