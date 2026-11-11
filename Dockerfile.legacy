FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Necessário para o comando pdftotext do extractor.py
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       poppler-utils \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY extractor.py .

# Executar com usuário sem privilégios
RUN useradd --create-home --uid 10001 shirley \
    && chown -R shirley:shirley /app

USER shirley

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \
    --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
