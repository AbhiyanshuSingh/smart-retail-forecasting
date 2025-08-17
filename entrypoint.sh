# #!/usr/bin/env bash
# set -euo pipefail

# echo "[entrypoint] Starting container…"

# # Create data dirs
# mkdir -p /app/data/raw /app/data/processed

# # If SAS URLs are provided, download recursively
# if [[ -n "${RAW_SAS_URL:-}" ]]; then
#   echo "[entrypoint] Downloading RAW data from SAS…"
#   azcopy cp "${RAW_SAS_URL}/*" "/app/data/raw" --recursive
# else
#   echo "[entrypoint] RAW_SAS_URL not set. Skipping RAW download."
# fi

# if [[ -n "${PROCESSED_SAS_URL:-}" ]]; then
#   echo "[entrypoint] Downloading PROCESSED data from SAS…"
#   azcopy cp "${PROCESSED_SAS_URL}/*" "/app/data/processed" --recursive
# else
#   echo "[entrypoint] PROCESSED_SAS_URL not set. Skipping PROCESSED download."
# fi

# # Quick sanity check for one known-needed file
# if [[ ! -f "/app/data/raw/calendar.csv" ]]; then
#   echo "[entrypoint] WARNING: /app/data/raw/calendar.csv not found. Listing /app/data for debugging:"
#   ls -R /app/data || true
# fi

# # Respect $PORT if Azure sets it; default to 8000
# APP_PORT="${PORT:-8000}"

# echo "[entrypoint] Launching Uvicorn on 0.0.0.0:${APP_PORT}…"
# exec uvicorn app_nolag:app --host 0.0.0.0 --port "${APP_PORT}"


####################################- github release -####################################

#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Starting container…"

mkdir -p /app/data/raw /app/data/processed

download_zip () {
  local url="$1"
  local out="$2"
  if [[ -z "${url:-}" ]]; then
    echo "[entrypoint] Skipping download for $out (no URL set)."
    return 0
  fi

  echo "[entrypoint] Downloading $out …"
  curl -fSL -o "$out" "$url"
}

# === Replace these with your actual GitHub Release URLs ===
RAW_URL="https://github.com/AbhiyanshuSingh/smart-retail-forecasting/releases/download/data-17-08-2025/raw.zip"
PROC_URL="https://github.com/AbhiyanshuSingh/smart-retail-forecasting/releases/download/data-17-08-2025/processed.zip"
# ==========================================================

# Download
download_zip "$RAW_URL"  "/tmp/raw.zip"
download_zip "$PROC_URL" "/tmp/processed.zip"

# Unzip
if [[ -f /tmp/raw.zip ]]; then
  echo "[entrypoint] Unzipping raw.zip → /app/data/raw"
  unzip -q -o /tmp/raw.zip -d /app/data/raw
fi

if [[ -f /tmp/processed.zip ]]; then
  echo "[entrypoint] Unzipping processed.zip → /app/data/processed"
  unzip -q -o /tmp/processed.zip -d /app/data/processed
fi

# Fix common mistake: nested raw/raw or processed/processed
shopt -s dotglob nullglob
if [[ -d /app/data/raw/raw ]]; then
  echo "[entrypoint] Detected nested raw/raw → flattening"
  mv /app/data/raw/raw/* /app/data/raw/ || true
  rmdir /app/data/raw/raw || true
fi
if [[ -d /app/data/processed/processed ]]; then
  echo "[entrypoint] Detected nested processed/processed → flattening"
  mv /app/data/processed/processed/* /app/data/processed/ || true
  rmdir /app/data/processed/processed || true
fi

echo "[entrypoint] Data layout after download:"
ls -lahR /app/data || true

# Sanity checks
RAW_OK=0
[[ -f /app/data/raw/calendar.csv ]] && RAW_OK=1 || echo "[entrypoint] WARNING: /app/data/raw/calendar.csv not found"
PROC_OK=0
[[ -f /app/data/processed/train_features.parquet ]] && PROC_OK=1 || echo "[entrypoint] WARNING: /app/data/processed/train_features.parquet not found"

if [[ "$RAW_OK" -ne 1 || "$PROC_OK" -ne 1 ]]; then
  echo "[entrypoint] ERROR: Required files missing. Check your zips and URLs."
  exit 1
fi

echo "[entrypoint] Launching Uvicorn on 0.0.0.0:${PORT:-8000}…"
exec uvicorn "${APP_MODULE:-app_nolag:app}" --host 0.0.0.0 --port "${PORT:-8000}"

