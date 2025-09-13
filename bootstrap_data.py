# # bootstrap_data.py
# import os
# from pathlib import Path
# from typing import Iterable

# from azure.identity import DefaultAzureCredential
# from azure.storage.blob import BlobServiceClient

# def _blob_service_client() -> BlobServiceClient:
#     #account_url = os.environ["https://smartretailforecasting.blob.core.windows.net/smart-retail-forecasting"]  # e.g., https://acct.blob.core.windows.net
#     account_url = os.environ["STORAGE_ACCOUNT_URL"]  # e.g., https://acct.blob.core.windows.net
#     # Prefer Managed Identity; DefaultAzureCredential will use it in App Service
#     cred = DefaultAzureCredential(exclude_interactive_browser_credential=True)
#     return BlobServiceClient(account_url=account_url, credential=cred)

# def _dest_base() -> Path:
#     # Put data under the app folder so existing relative paths like data/raw/... still work
#     here = Path(__file__).resolve().parent
#     dest = here / "data"
#     dest.mkdir(parents=True, exist_ok=True)
#     return dest

# def _mirror_prefix(container_name: str, prefix: str, dest_root: Path) -> None:
#     bsc = _blob_service_client()
#     container = bsc.get_container_client(container_name)
#     # iterate all blobs under prefix (folders are virtual)
#     for blob in container.list_blobs(name_starts_with=prefix):
#         target = dest_root / Path(blob.name)  # preserves raw/... or processed/...
#         target.parent.mkdir(parents=True, exist_ok=True)
#         downloader = container.download_blob(blob.name)
#         with open(target, "wb") as f:
#             downloader.readinto(f)

# def ensure_data():
#     """
#     Download raw/ and processed/ prefixes to ./data if the key files are missing.
#     Safe to call multiple times; quick if files already exist.
#     """
#     container = os.environ.get("BLOB_CONTAINER_NAME", "smart-retail-forecasting")
#     prefixes_env = os.environ.get("BLOB_PREFIXES", "raw/,processed/")
#     prefixes: Iterable[str] = [p.strip() for p in prefixes_env.split(",") if p.strip()]

#     dest = _dest_base()
#     # If your code requires these two, check first to avoid extra work if already present
#     key1 = dest / "raw" / "calendar.csv"
#     key2 = dest / "processed" / "train_features.parquet"
#     if key1.exists() and key2.exists():
#         return

#     for p in prefixes:
#         _mirror_prefix(container, p, dest)






# bootstrap_data.py
import os
from pathlib import Path
from typing import Iterable

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

def _blob_service_client() -> BlobServiceClient:
    """
    Create a BlobServiceClient using either:
    1. Managed Identity / DefaultAzureCredential (preferred in Azure), or
    2. SAS token from STORAGE_SAS_TOKEN (fallback for local/testing).
    """
    account_url = os.environ["STORAGE_ACCOUNT_URL"]  # e.g., https://acct.blob.core.windows.net
    sas_token = os.environ.get("STORAGE_SAS_TOKEN")

    if sas_token:
        print("[bootstrap] Using SAS token for BlobServiceClient")
        return BlobServiceClient(account_url=account_url, credential=sas_token)

    print("[bootstrap] Using DefaultAzureCredential for BlobServiceClient")
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    return BlobServiceClient(account_url=account_url, credential=cred)

def _dest_base() -> Path:
    here = Path(__file__).resolve().parent
    dest = here / "data"
    dest.mkdir(parents=True, exist_ok=True)
    return dest

def _mirror_prefix(container_name: str, prefix: str, dest_root: Path) -> None:
    bsc = _blob_service_client()
    container = bsc.get_container_client(container_name)
    for blob in container.list_blobs(name_starts_with=prefix):
        target = dest_root / Path(blob.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            print(f"[bootstrap] Downloading {blob.name} → {target}")
            downloader = container.download_blob(blob.name)
            with open(target, "wb") as f:
                downloader.readinto(f)

def ensure_data():
    container = os.environ.get("BLOB_CONTAINER_NAME", "retail-forecasting")
    prefixes_env = os.environ.get("BLOB_PREFIXES", "data/raw/,data/processed/")
    prefixes: Iterable[str] = [p.strip() for p in prefixes_env.split(",") if p.strip()]

    dest = _dest_base()
    key1 = dest / "raw" / "calendar.csv"
    key2 = dest / "processed" / "train_features.parquet"

    if key1.exists() and key2.exists():
        print("[bootstrap] Key files already present, skipping download.")
        return

    for p in prefixes:
        _mirror_prefix(container, p, dest)
