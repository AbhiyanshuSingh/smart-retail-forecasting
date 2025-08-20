#!/bin/sh
set -euo pipefail

echo "[entrypoint] Starting container with bundled data…"

# Sanity checks
RAW_OK=0
[[ -f /app/data/raw/calendar.csv ]] && RAW_OK=1 || echo "[entrypoint] WARNING: /app/data/raw/calendar.csv not found"
PROC_OK=0
[[ -f /app/data/processed/train_features.parquet ]] && PROC_OK=1 || echo "[entrypoint] WARNING: /app/data/processed/train_features.parquet not found"

if [[ "$RAW_OK" -ne 1 || "$PROC_OK" -ne 1 ]]; then
  echo "[entrypoint] ERROR: Required files missing in image. Did you COPY them in Dockerfile?"
  exit 1
fi

echo "[entrypoint] Launching Uvicorn on 0.0.0.0:${PORT:-8080}…"
exec uvicorn "${APP_MODULE:-app_nolag:app}" --host 0.0.0.0 --port "${PORT:-8080}"
