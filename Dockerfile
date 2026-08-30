FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db/ db/
COPY etl/ etl/
COPY api/ api/
COPY frontend/ frontend/

EXPOSE 8000

CMD python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
