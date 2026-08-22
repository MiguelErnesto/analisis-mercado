from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from etl.dbconfig import pg_kwargs


@contextmanager
def get_conn():
    conn = psycopg.connect(**pg_kwargs(), row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()
