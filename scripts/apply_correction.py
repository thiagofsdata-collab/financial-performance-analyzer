import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.generate_data import generate_transactions, save_raw
from src.ingest import BUCKET_NAME, upload_if_new
from src.merge import load_to_staging, merge_staging_into_target

# Must be a month originally loaded through the isolated single-month
# generation path (scripts/ingest_incremental.py, M7) — i.e. one of the
# 2024 months, not a 2023 one. generate_transactions(year_month=...)
# resets the RNG seed fresh before generating; regenerating a 2023 month
# in isolation produces DIFFERENT values than it originally had, because
# the historical 2023 backfill (M5/M6) generated all 12 months in one
# continuous seeded loop, where the random state had already advanced
# through every earlier month before reaching this one. Regenerating a
# 2024 month matches exactly, since it was loaded the same isolated way.
CORRECTED_MONTH = "2024-01"
RESTATEMENT_DELTA = Decimal("500.00")


def run() -> None:
    df = generate_transactions(year_month=CORRECTED_MONTH)

    original_amount = df.loc[0, "amount"]
    df.loc[0, "amount"] = original_amount + RESTATEMENT_DELTA
    corrected_id = df.loc[0, "transaction_id"]
    print(f"restatement: transaction_id={corrected_id} amount {original_amount} -> {df.loc[0, 'amount']}")

    local_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "transactions.parquet")
    save_raw(df)

    upload_result = upload_if_new(local_path, year_month=CORRECTED_MONTH)
    gcs_uri = f"gs://{BUCKET_NAME}/{upload_result['path']}"

    load_to_staging(gcs_uri)
    merge_staging_into_target()


if __name__ == "__main__":
    run()
