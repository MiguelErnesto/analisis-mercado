import os


def pg_kwargs(dbname=None):
    return {
        "host": os.environ["POSTGRES_HOST"],
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "dbname": dbname or os.environ.get("POSTGRES_DB", "analisis_mercado"),
    }


def admin_db():
    return os.environ.get("POSTGRES_ADMIN_DB", "postgres")
