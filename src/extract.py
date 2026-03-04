import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "financial_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")


def extract_transactions(start_date, end_date):
    engine = get_connection()
    query = """
        SELECT *
        FROM transactions
        WHERE date BETWEEN :start AND :end
        ORDER BY date
    """
    df = pd.read_sql(
        text(query),
        engine,
        params={"start": start_date, "end": end_date}
    )
    return df

def save_raw(df,path):
    df.to_parquet(path, index=False)



if __name__ == "__main__":
    df = extract_transactions("2023-01-01", "2023-12-31")
    path = "data/raw/transactions.parquet"
    save_raw(df, path)
    print(f"{len(df):,} rows extracted")