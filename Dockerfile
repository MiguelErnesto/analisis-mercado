FROM debian:latest

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY db/ db/
COPY etl/ etl/
COPY api/ api/
COPY frontend/ frontend/

EXPOSE 8000

CMD python3 -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
