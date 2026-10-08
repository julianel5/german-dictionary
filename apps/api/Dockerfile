# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /repo

COPY pyproject.toml README.md ./
COPY apps/api ./apps/api
COPY services ./services
COPY scripts ./scripts
COPY data/fixtures ./data/fixtures

RUN pip install --no-cache-dir -e . \
    && python -m spacy download de_core_news_sm

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
