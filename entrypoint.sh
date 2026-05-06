#!/bin/bash
set -e

exec uvicorn src.app.main:app \
  --host 0.0.0.0 \
  --workers 1 \
  --port ${PORT:-8000}
