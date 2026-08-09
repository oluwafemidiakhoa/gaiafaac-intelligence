FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/api /app
COPY alembic.ini /app/alembic.ini
COPY database/migrations /app/database/migrations
COPY database/seeds /app/database/seeds
RUN pip install --no-cache-dir ".[extraction]"

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn gaiafaac_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
