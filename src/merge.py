import os

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "financial-perf-analyzer")
TARGET_TABLE = f"{GCP_PROJECT_ID}.raw.transactions"
STAGING_TABLE = f"{GCP_PROJECT_ID}.raw.transactions_staging"

TRANSACTION_COLUMNS = [
    "transaction_id",
    "date",
    "company",
    "business_unit",
    "cost_center",
    "account_code",
    "account_name",
    "dre_line",
    "amount",
]


def load_to_staging(gcs_uri: str, table_id: str = STAGING_TABLE) -> None:
    """
    Loads a batch into the staging table, replacing whatever was there
    before (WRITE_TRUNCATE) — staging only ever holds the current batch
    being merged, never accumulated history like the target table.
    """
    client = bigquery.Client(project=GCP_PROJECT_ID)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()
    print(f"STAGING LOAD: {gcs_uri} -> {table_id} ({load_job.output_rows} rows)")


def merge_staging_into_target(target_table: str = TARGET_TABLE, staging_table: str = STAGING_TABLE) -> int:
    """
    MERGE staging (source) into target (raw.transactions), matched on
    transaction_id: a matching row gets its columns overwritten (a
    correction/restatement); a non-matching row gets inserted as new.

    Idempotent by construction: running the exact same MERGE again finds
    the same matches and sets the same values — no duplication, no drift.
    """
    update_set = ", ".join(f"target.{c} = source.{c}" for c in TRANSACTION_COLUMNS if c != "transaction_id")
    insert_cols = ", ".join(TRANSACTION_COLUMNS)
    insert_values = ", ".join(f"source.{c}" for c in TRANSACTION_COLUMNS)

    query = f"""
    MERGE `{target_table}` AS target
    USING `{staging_table}` AS source
    ON target.transaction_id = source.transaction_id
    WHEN MATCHED THEN
      UPDATE SET {update_set}
    WHEN NOT MATCHED THEN
      INSERT ({insert_cols})
      VALUES ({insert_values})
    """
    client = bigquery.Client(project=GCP_PROJECT_ID)
    job = client.query(query)
    job.result()
    print(f"MERGE: {job.num_dml_affected_rows} linha(s) afetada(s)")
    return job.num_dml_affected_rows
