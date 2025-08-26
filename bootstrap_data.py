# bootstrap_data.py
import os
from pathlib import Path
from typing import Iterable

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

def _blob_service_client() -> BlobServiceClient:
    #account_url = os.environ["https://smartretailforecasting.blob.core.windows.net/smart-retail-forecasting"]  # e.g., https://acct.blob.core.windows.net
    account_url = os.environ["STORAGE_ACCOUNT_URL"]  # e.g., https://acct.blob.core.windows.net
    # Prefer Managed Identity; DefaultAzureCredential will use it in App Service
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    return BlobServiceClient(account_url=account_url, credential=cred)

def _dest_base() -> Path:
    # Put data under the app folder so existing relative paths like data/raw/... still work
    here = Path(__file__).resolve().parent
    dest = here / "data"
    dest.mkdir(parents=True, exist_ok=True)
    return dest

def _mirror_prefix(container_name: str, prefix: str, dest_root: Path) -> None:
    bsc = _blob_service_client()
    container = bsc.get_container_client(container_name)
    # iterate all blobs under prefix (folders are virtual)
    for blob in container.list_blobs(name_starts_with=prefix):
        target = dest_root / Path(blob.name)  # preserves raw/... or processed/...
        target.parent.mkdir(parents=True, exist_ok=True)
        downloader = container.download_blob(blob.name)
        with open(target, "wb") as f:
            downloader.readinto(f)

def ensure_data():
    """
    Download raw/ and processed/ prefixes to ./data if the key files are missing.
    Safe to call multiple times; quick if files already exist.
    """
    container = os.environ.get("BLOB_CONTAINER_NAME", "smart-retail-forecasting")
    prefixes_env = os.environ.get("BLOB_PREFIXES", "raw/,processed/")
    prefixes: Iterable[str] = [p.strip() for p in prefixes_env.split(",") if p.strip()]

    dest = _dest_base()
    # If your code requires these two, check first to avoid extra work if already present
    key1 = dest / "raw" / "calendar.csv"
    key2 = dest / "processed" / "train_features.parquet"
    if key1.exists() and key2.exists():
        return

    for p in prefixes:
        _mirror_prefix(container, p, dest)
