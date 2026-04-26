FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=".:./src"
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

COPY . .

ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p /app/.cache/huggingface && \
    chown -R appuser:appgroup /app/.cache

COPY --chown=appuser:appgroup . .
RUN chmod +x /app/entrypoint.sh

USER appuser

ARG PORT=8000
EXPOSE ${PORT}

CMD ["./entrypoint.sh"]