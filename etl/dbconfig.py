import os
from urllib.parse import parse_qs, unquote, urlparse


def managed_postgres() -> bool:
    return bool(os.environ.get("DATABASE_URL") or os.environ.get("RAILWAY_ENVIRONMENT"))


def pg_kwargs(dbname=None):
    url = os.environ.get("DATABASE_URL")
    if url:
        return _from_url(url, dbname)
    kwargs = {
        "host": os.environ["POSTGRES_HOST"],
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "dbname": dbname or os.environ.get("POSTGRES_DB", "analisis_mercado"),
    }
    sslmode = os.environ.get("POSTGRES_SSLMODE")
    if sslmode:
        kwargs["sslmode"] = sslmode
    elif os.environ.get("RAILWAY_ENVIRONMENT"):
        kwargs["sslmode"] = "require"
    return kwargs


def _from_url(url: str, dbname=None) -> dict:
    parsed = urlparse(url)
    kwargs = {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "dbname": dbname or parsed.path.lstrip("/") or os.environ.get("POSTGRES_DB", "analisis_mercado"),
    }
    qs = parse_qs(parsed.query)
    if "sslmode" in qs:
        kwargs["sslmode"] = qs["sslmode"][0]
    else:
        kwargs["sslmode"] = os.environ.get("POSTGRES_SSLMODE", "require")
    return kwargs


def admin_db():
    return os.environ.get("POSTGRES_ADMIN_DB", "postgres")
