#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Starting container…"

# Create data dirs
mkdir -p /app/data/raw /app/data/processed

# If SAS URLs are provided, download recursively
if [[ -n "${RAW_SAS_URL:-}" ]]; then
  echo "[entrypoint] Downloading RAW data from SAS…"
  azcopy cp "${RAW_SAS_URL}" "/app/data/raw" --recursive
else
  echo "[entrypoint] RAW_SAS_URL not set. Skipping RAW download."
fi

if [[ -n "${PROCESSED_SAS_URL:-}" ]]; then
  echo "[entrypoint] Downloading PROCESSED data from SAS…"
  azcopy cp "${PROCESSED_SAS_URL}" "/app/data/processed" --recursive
else
  echo "[entrypoint] PROCESSED_SAS_URL not set. Skipping PROCESSED download."
fi

# Quick sanity check for one known-needed file
if [[ ! -f "/app/data/raw/calendar.csv" ]]; then
  echo "[entrypoint] WARNING: /app/data/raw/calendar.csv not found. Listing /app/data for debugging:"
  ls -R /app/data || true
fi

# Respect $PORT if Azure sets it; default to 8000
APP_PORT="${PORT:-8000}"

echo "[entrypoint] Launching Uvicorn on 0.0.0.0:${APP_PORT}…"
exec uvicorn app_nolag:app --host 0.0.0.0 --port "${APP_PORT}"
