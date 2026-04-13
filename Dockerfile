FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY migrations /app/migrations
COPY alembic.ini /app/

RUN pip install --upgrade pip \
    && pip install -e .

COPY . /app

CMD ["uvicorn", "docustruct_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
