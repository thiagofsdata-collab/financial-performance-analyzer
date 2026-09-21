import hashlib
import os
import re

from dotenv import load_dotenv
from google.cloud import bigquery, storage

load_dotenv()

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "financial-perf-analyzer-raw")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "financial-perf-analyzer")
BIGQUERY_TABLE = f"{GCP_PROJECT_ID}.raw.transactions"

MONTH_PREFIX_RE = re.compile(r"month=(\d{4}-\d{2})/")


def compute_file_hash(path: str) -> str:
    """SHA256 of the file's bytes — the content identity used for dedup."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def build_object_path(file_hash: str, year_month: str) -> str:
    """
    Content-addressed object path: raw/transactions/month=<YYYY-MM>/<hash>.parquet

    The path encodes what period the DATA inside the file covers (month),
    not when the ingestion script happened to run — that distinction
    matters because get_latest_ingested_month() below reads this path to
    answer "what's already been extracted?", a question about the data's
    content, not about run history.

    The hash makes the object name itself the identity check — no separate
    manifest file needed. "Already ingested?" reduces to "does an object
    already exist at this exact path?"
    """
    return f"raw/transactions/month={year_month}/{file_hash}.parquet"


def get_latest_ingested_month(bucket_name: str = BUCKET_NAME) -> str | None:
    """
    Extraction watermark: the most recent "YYYY-MM" already present in the
    GCS landing zone, read directly from existing object paths.

    Deliberately does NOT ask BigQuery. "What have I already extracted?"
    is a question about the landing zone, not about the warehouse — a file
    can be sitting in GCS, already extracted, before it's ever loaded into
    BigQuery. Asking the warehouse for this would conflate extraction
    state with load state and risk re-extracting a month that is already
    in GCS but simply hasn't been loaded yet.
    """
    client = storage.Client()
    months = set()
    for blob in client.list_blobs(bucket_name, prefix="raw/transactions/"):
        match = MONTH_PREFIX_RE.search(blob.name)
        if match:
            months.add(match.group(1))
    return max(months) if months else None


def upload_if_new(local_path: str, year_month: str, bucket_name: str = BUCKET_NAME) -> dict:
    """
    Uploads local_path to GCS at a content-addressed path, skipping the
    upload if that exact content has already landed there.

    Idempotency: re-running ingestion on unchanged content is a no-op, not
    a duplicate — the object path is derived from the file's SHA256, so the
    same bytes always resolve to the same path.
    """
    file_hash = compute_file_hash(local_path)
    object_path = build_object_path(file_hash, year_month)

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)

    if blob.exists():
        print(f"SKIP (ja ingerido, hash identico): gs://{bucket_name}/{object_path}")
        return {"uploaded": False, "path": object_path, "hash": file_hash}

    blob.upload_from_filename(local_path)
    print(f"UPLOAD: gs://{bucket_name}/{object_path}")
    return {"uploaded": True, "path": object_path, "hash": file_hash}


def load_to_bigquery(object_path: str, bucket_name: str = BUCKET_NAME, table_id: str = BIGQUERY_TABLE) -> bool:
    """
    Appends the GCS object into the BigQuery table, unless it already
    carries a "loaded_to_bq" marker in its own blob metadata.

    Why this check exists: GCS's hash-based path (upload_if_new) prevents
    the same content from being uploaded to GCS twice, but says nothing
    about whether that object has already been loaded into BigQuery — a
    load job can be re-run against a file that landed successfully days
    ago. Tracking "loaded" state as metadata on the object itself keeps
    that state next to the data it describes, with no separate manifest
    table to keep in sync.

    Returns True if a load actually ran, False if it was skipped.
    """
    client = storage.Client()
    blob = client.bucket(bucket_name).get_blob(object_path)

    if blob.metadata and blob.metadata.get("loaded_to_bq") == "true":
        print(f"SKIP (ja carregado no BigQuery): gs://{bucket_name}/{object_path}")
        return False

    bq_client = bigquery.Client(project=GCP_PROJECT_ID)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    uri = f"gs://{bucket_name}/{object_path}"
    load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)
    load_job.result()
    print(f"LOAD: {uri} -> {table_id} ({load_job.output_rows} rows)")

    blob.metadata = {**(blob.metadata or {}), "loaded_to_bq": "true"}
    blob.patch()
    return True


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "transactions.parquet")
    upload_if_new(path, year_month="2023-01")
