import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.generate_data import generate_transactions, save_raw
from src.ingest import get_latest_ingested_month, get_unloaded_objects, load_to_bigquery, upload_if_new

# 2023 (all 12 months) was already bulk-loaded into BigQuery as a one-time
# historical backfill in M5/M6. This incremental path picks up from there —
# it is not meant to re-derive 2023 through the per-month GCS convention.
FIRST_INCREMENTAL_MONTH = "2024-01"


def _next_month(year_month: str) -> str:
    year, month = (int(part) for part in year_month.split("-"))
    if month == 12:
        return f"{year + 1}-01"
    return f"{year}-{month + 1:02d}"


def run() -> None:
    watermark = get_latest_ingested_month()
    print(f"watermark (ultimo mes no GCS): {watermark or '(nenhum)'}")

    if watermark is not None:
        pending = get_unloaded_objects(watermark)
        if pending:
            print(f"{watermark} ja esta no GCS mas nao foi carregado no BigQuery — retomando antes de avancar")
            for object_path in pending:
                load_to_bigquery(object_path)
            return

    next_month = FIRST_INCREMENTAL_MONTH if watermark is None else _next_month(watermark)
    print(f"proximo mes a processar: {next_month}")

    df = generate_transactions(year_month=next_month)
    local_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "transactions.parquet")
    save_raw(df)

    upload_result = upload_if_new(local_path, year_month=next_month)
    load_to_bigquery(upload_result["path"])


if __name__ == "__main__":
    run()
