from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg import ClientCursor, sql

from etl.dbconfig import admin_db, pg_kwargs
from etl.generate_data import generate

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "db" / "schema.sql"


def ensure_database() -> None:
    target = pg_kwargs()["dbname"]
    with psycopg.connect(**pg_kwargs(admin_db()), autocommit=True) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (target,),
        ).fetchone()
        if not exists:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target)))
            print(f"Creada base {target}")
        else:
            print(f"Base {target} ya existe")


def apply_schema() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with psycopg.connect(**pg_kwargs(), cursor_factory=ClientCursor) as conn:
        conn.execute(schema)
        conn.commit()
    print("Schema aplicado")


def _copy_df(conn, table: str, columns: list[str], df) -> None:
    with conn.cursor() as cur:
        with cur.copy(
            sql.SQL("COPY {} ({}) FROM STDIN").format(
                sql.Identifier(table),
                sql.SQL(", ").join(sql.Identifier(c) for c in columns),
            )
        ) as copy:
            for row in df.itertuples(index=False, name=None):
                copy.write_row(row)


def load_all() -> None:
    data = generate()
    with psycopg.connect(**pg_kwargs()) as conn:
        _copy_df(conn, "stores", ["id", "name", "region", "lat", "lon"], data["stores"])
        _copy_df(conn, "products", ["id", "name", "category"], data["products"])
        _copy_df(conn, "holidays", ["date", "name"], data["holidays"])
        _copy_df(
            conn,
            "sales",
            ["date", "store_id", "product_id", "qty", "revenue", "promo"],
            data["sales"],
        )
        conn.commit()
    print(f"Cargadas {len(data['sales']):,} líneas de venta")
