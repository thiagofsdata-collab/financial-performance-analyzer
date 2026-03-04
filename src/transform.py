import pandas as pd

def load_raw(path):
    df = pd.read_parquet(path)
    return df

def build_dre(df):
    df = df.groupby(['company','date','dre_line'])["amount"].sum().unstack("dre_line").reset_index()
    
    df["Receita Liquida"] = df["Receita Bruta"] + df["Deducoes da Receita"]
    df["Lucro Bruto"] = df["Receita Liquida"] + df["COGS"]
    df["EBITDA"] = df["Lucro Bruto"] + df["Opex"]
    df["Lucro Liquido"] = df["EBITDA"] + df["Resultado Financeiro"] + df["Impostos"]
    
    return df

def calculate_margins(df):
    df['gross_margin']  = df['Lucro Bruto'] / df['Receita Bruta']
    df['ebitda_margin'] = df['EBITDA'] / df['Receita Bruta']
    df['net_margin'] = df['Lucro Liquido'] / df['Receita Bruta']
    return df


def calculate_variance(df):
    df = df.sort_values(["company", "date"])
    
    for col in ["Receita Bruta", "Lucro Bruto", "EBITDA"]:
        df[f"{col}_mom"] = (
            df.groupby("company")[col].pct_change(periods=1)
        )
        df[f"{col}_yoy"] = (
            df.groupby("company")[col].pct_change(periods=12)
        ) #Nan
    
    return df


def save_processed(df,path):
    df.to_parquet(path, index=False)


if __name__ == "__main__":
    raw_path = "data/raw/transactions.parquet"
    out_path = "data/processed/dre_metrics.parquet"

    df_raw = load_raw(raw_path)
    dre_df = build_dre(df_raw)
    metrics_df = calculate_margins(dre_df)
    metrics_df = calculate_variance(metrics_df)

    save_processed(metrics_df, out_path)
    print(metrics_df.shape)