import os
import pandas as pd
import numpy as np
from datetime import date
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

print("script loaded")

def get_engine():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "financial_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")



# Chart of accounts based on the standard structure of Brazilian income statement (CPC 26 / NBC TG 26)
# Proportions calibrated from the Kaggle dataset: rish59/financial-statements-of-major-companies2009-2023
# IT: gross margin 57%, EBITDA 36% | FOOD: gross margin 45%, EBITDA 42%

ACCOUNT_MAPPING = [
    # (account_code, account_name, dre_line, dre_order, sign, pct_of_gross_revenue)
    # sign: +1 revenue, -1 costs/deductions
    ("4.1.01", "Venda de Produtos",           "Receita Bruta",        1, +1, 0.75),
    ("4.1.02", "Venda de Servicos",            "Receita Bruta",        1, +1, 0.25),
    ("5.1.01", "Devolucoes de Vendas",         "Deducoes da Receita",  2, -1, 0.05),
    ("5.1.02", "Impostos sobre Vendas",        "Deducoes da Receita",  2, -1, 0.07),
    ("6.1.01", "Custo dos Produtos Vendidos",  "COGS",                 3, -1, 0.38),
    ("6.1.02", "Custo dos Servicos",           "COGS",                 3, -1, 0.07),
    ("7.1.01", "Despesas com Pessoal",         "Opex",                 4, -1, 0.14),
    ("7.1.02", "Despesas Administrativas",     "Opex",                 4, -1, 0.06),
    ("7.1.03", "Despesas com Marketing",       "Opex",                 4, -1, 0.04),
    ("7.1.04", "Despesas Logisticas",          "Opex",                 4, -1, 0.03),
    ("8.1.01", "Receitas Financeiras",         "Resultado Financeiro", 5, +1, 0.02),
    ("8.1.02", "Despesas Financeiras",         "Resultado Financeiro", 5, -1, 0.03),
    ("9.1.01", "Imposto de Renda (IRPJ)",      "Impostos",             6, -1, 0.02),
    ("9.1.02", "Contribuicao Social (CSLL)",   "Impostos",             6, -1, 0.01),
]


COMPANIES = {
    "Company A": 8_000_000,
    "Company B": 3_000_000,
}

BU_WEIGHTS = {
    "Retail": 0.50,
    "Wholesale": 0.30,
    "E-commerce": 0.20,
}

COST_CENTERS = {
    "Retail": [
        "Retail - Stores",
        "Retail - Operations",
        "Retail - Regional Management",
    ],
    
    "Wholesale": [
        "Wholesale - Sales",
        "Wholesale - Distribution",
    ],
    
    "E-commerce": [
        "Ecom - Platform",
        "Ecom - Marketing",
        "Ecom - Fulfillment",
    ],
}


MONTHS = [date(2023, m, 1) for m in range(1, 13)]


def generate_transactions() -> pd.DataFrame:
    """
    Generate synthetic financial transactions.

    Creates transaction records across companies, business units,
    cost centers, and accounts for each month of the year,
    applying proportional weights and random noise.
    """
    np.random.seed(42)
    rows = []

    for month in MONTHS:
        for company, base_revenue in COMPANIES.items():
            for bu, bu_weight in BU_WEIGHTS.items():
                cost_centers = COST_CENTERS[bu]
                cc_weight = 1 / len(cost_centers)

                for cc in cost_centers:
                    for code, name, dre_line, order, sign, pct in ACCOUNT_MAPPING:
                        base = base_revenue * bu_weight * cc_weight * pct
                        noise = np.random.uniform(0.85, 1.15)
                        amount = round(base * noise * sign, 2)

                        rows.append({
                            "date": month,
                            "company": company,
                            "business_unit": bu,
                            "cost_center": cc,
                            "account_code": code,
                            "account_name": name,
                            "dre_line": dre_line,
                            "amount": amount,
                        })

    return pd.DataFrame(rows)



def load_schema(engine):
    """
    Load and execute the database schema SQL file.

    Reads the schema definition from sql/01_schema.sql and executes it
    using the provided SQLAlchemy engine to create the required tables.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "01_schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("schema created")



def load_account_mapping(engine):
    """
    Insert the chart of accounts into the account_mapping table.

    Converts the ACCOUNT_MAPPING constant into a DataFrame and inserts
    the records into the PostgreSQL table using the provided engine.
    """
    rows = [
        {"account_code": code, "account_name": name, "dre_line": dre,
         "dre_order": order, "amount_sign": sign}
        for code, name, dre, order, sign, _ in ACCOUNT_MAPPING
    ]
    pd.DataFrame(rows).to_sql("account_mapping", engine, if_exists="append", index=False)
    print(f"account_mapping: {len(rows)} accounts inserted")



def load_transactions(engine, df):
    """
    Insert generated transaction records into the transactions table.

    Takes a DataFrame containing synthetic financial transactions and
    appends them to the transactions table in PostgreSQL.
    """
    df.to_sql("transactions", engine, if_exists="append", index=False)
    print(f"transactions: {len(df):,} rows inserted")



def save_raw(df):
    """
    Save generated transactions as a raw parquet file.

    Writes the DataFrame of synthetic transactions to
    data/raw/transactions.parquet for downstream processing.
    """
    path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "transactions.parquet")
    df.to_parquet(path, index=False)
    print(f"raw parquet saved to data/raw/transactions.parquet")



if __name__ == "__main__":
    print("generating transactions...")
    df = generate_transactions()
    print(f"{len(df):,} rows generated")

    engine = get_engine()
    load_schema(engine)
    load_account_mapping(engine)
    load_transactions(engine, df)
    save_raw(df)