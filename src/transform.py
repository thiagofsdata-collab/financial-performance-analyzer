import pandas as pd

def load_raw(path):
    """
    Loads a Parquet file from the given path.

    Args:
        path (str): path to the Parquet file

    Returns:
        pd.DataFrame: raw transactions
    """

    df = pd.read_parquet(path)
    return df

def build_dre(df):
    """
    Builds the aggregated income statement (DRE) by company and date.

    Groups transactions by company, date, and dre_line, pivots accounting
    lines into columns, and calculates the main financial indicators.

    Calculated indicators:
        - Receita Liquida (Net Revenue)
        - Lucro Bruto (Gross Profit)
        - EBITDA
        - Lucro Liquido (Net Income)

    Args:
        df (pd.DataFrame): raw transactions with columns:
            - company (str): company identifier
            - date (datetime): reference date
            - dre_line (str): income statement line
            - amount (float): monetary value

    Returns:
        pd.DataFrame: aggregated DataFrame with DRE lines as columns
            and calculated indicators
    """

    df = df.groupby(['company','date','dre_line'])["amount"].sum().unstack("dre_line").reset_index()
    
    df["Receita Liquida"] = df["Receita Bruta"] + df["Deducoes da Receita"]
    df["Lucro Bruto"] = df["Receita Liquida"] + df["COGS"]
    df["EBITDA"] = df["Lucro Bruto"] + df["Opex"]
    df["Lucro Liquido"] = df["EBITDA"] + df["Resultado Financeiro"] + df["Impostos"]
    
    return df

def calculate_margins(df):
    """
    Calculates financial margins from DRE indicators.

    All margins are calculated relative to Receita Bruta (Gross Revenue):
        - gross_margin  = Lucro Bruto / Receita Bruta
        - ebitda_margin = EBITDA / Receita Bruta
        - net_margin    = Lucro Liquido / Receita Bruta

    Args:
        df (pd.DataFrame): DataFrame containing at minimum:
            - Receita Bruta (float)
            - Lucro Bruto (float)
            - EBITDA (float)
            - Lucro Liquido (float)

    Returns:
        pd.DataFrame: original DataFrame with margin columns added
    """

    df['gross_margin']  = df['Lucro Bruto'] / df['Receita Bruta']
    df['ebitda_margin'] = df['EBITDA'] / df['Receita Bruta']
    df['net_margin'] = df['Lucro Liquido'] / df['Receita Bruta']
    return df


def calculate_variance(df):
    """
    Calculates MoM and YoY percentage changes for key financial metrics.

    Sorts data by company and date, then calculates:
        - MoM (month-over-month): change relative to the previous period
        - YoY (year-over-year): change relative to the same period last year

    Metrics analyzed:
        - Receita Bruta
        - Lucro Bruto
        - EBITDA

    Args:
        df (pd.DataFrame): DataFrame containing:
            - company (str): company identifier
            - date (datetime): reference date
            - Receita Bruta, Lucro Bruto, EBITDA (float)

    Returns:
        pd.DataFrame: DataFrame with additional columns:
            - <metric>_mom (float)
            - <metric>_yoy (float)

    Notes:
        - First periods will have NaN due to absence of a comparison base
        - YoY assumes monthly frequency (lag of 12 periods)
    """

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
    """
    Saves the processed DataFrame as a Parquet file.

    Args:
        df (pd.DataFrame): DataFrame to persist
        path (str): destination file path

    Returns:
        None
    """

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