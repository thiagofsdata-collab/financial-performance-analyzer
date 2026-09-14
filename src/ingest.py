import hashlib
import os
from datetime import date

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "financial-perf-analyzer-raw")


def compute_file_hash(path: str) -> str:
    """SHA256 of the file's bytes — the content identity used for dedup."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def build_object_path(file_hash: str, ingestion_date: date) -> str:
    """
    Content-addressed object path: raw/transactions/dt=<ingestion date>/<hash>.parquet

    The hash makes the object name itself the identity check — no separate
    manifest file needed. "Already ingested?" reduces to "does an object
    already exist at this exact path?"
    """
    return f"raw/transactions/dt={ingestion_date.isoformat()}/{file_hash}.parquet"


def upload_if_new(local_path: str, bucket_name: str = BUCKET_NAME) -> dict:
    """
    Uploads local_path to GCS at a content-addressed path, skipping the
    upload if that exact content has already landed there.

    Idempotency: re-running ingestion on unchanged content is a no-op, not
    a duplicate — the object path is derived from the file's SHA256, so the
    same bytes always resolve to the same path.
    """
    file_hash = compute_file_hash(local_path)
    object_path = build_object_path(file_hash, date.today())

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)

    if blob.exists():
        print(f"SKIP (ja ingerido, hash identico): gs://{bucket_name}/{object_path}")
        return {"uploaded": False, "path": object_path, "hash": file_hash}

    blob.upload_from_filename(local_path)
    print(f"UPLOAD: gs://{bucket_name}/{object_path}")
    return {"uploaded": True, "path": object_path, "hash": file_hash}


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "transactions.parquet")
    upload_if_new(path)
