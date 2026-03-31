import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def load_processed(path):
    """
    Load a processed Parquet file.

    Args:
        path (str): Path to the Parquet file.

    Returns:
        pd.DataFrame: DataFrame with processed data.
    """
    df = pd.read_parquet(path)
    return df

def plot_margins(df):
    """
    Plot margin trends over time by company.

    Args:
        df (pd.DataFrame): DataFrame with date, company, and margin columns.

    Returns:
        plotly.graph_objects.Figure: Line chart of margins over time.
    """
    fig = px.line(
        df,
        x="date",
        y=["gross_margin", "ebitda_margin", "net_margin"],
        color="company",
        title="Margins over time",
        labels={"value": "Margin", "date": "Month"},
    )
    return fig

def plot_revenue(df):
    """
    Plot gross revenue by month and company.

    Args:
        df (pd.DataFrame): DataFrame with date, company, and revenue columns.

    Returns:
        plotly.graph_objects.Figure: Bar chart of gross revenue.
    """
    fig = px.bar(
        df,
        x="date",
        y="Receita Bruta",
        color="company",
        title="Gross Revenue by Month",
        labels={"Receita Bruta": "Revenue (R$)", "date": "Month"},
        barmode="group",
    )
    return fig


def plot_ebitda_waterfall(df):
    """
    Plot a full DRE waterfall bridge side by side for both companies.

    Args:
        df (pd.DataFrame): DataFrame with DRE line items as columns.
        company (str): Not used in this version — plots both companies.

    Returns:
        plotly.graph_objects.Figure: Side-by-side waterfall charts.
    """
    from plotly.subplots import make_subplots

    companies = df["company"].unique()

    fig = make_subplots(
        rows=1,
        cols=len(companies),
        subplot_titles=[f"DRE Bridge — {c} (Annual)" for c in companies],
    )

    labels = [
        "Receita Bruta",
        "Deducoes da Receita",
        "COGS",
        "Receita Liquida",
        "Opex",
        "EBITDA",
        "Resultado Financeiro",
        "Impostos",
        "Lucro Liquido",
    ]

    measures = [
        "absolute",
        "relative",
        "relative",
        "total",
        "relative",
        "total",
        "relative",
        "relative",
        "total",
    ]

    for i, comp in enumerate(companies):
        data = df[df["company"] == comp].sum(numeric_only=True)

        values = [
            data["Receita Bruta"],
            data["Deducoes da Receita"],
            data["COGS"],
            data["Receita Liquida"],
            data["Opex"],
            data["EBITDA"],
            data["Resultado Financeiro"],
            data["Impostos"],
            data["Lucro Liquido"],
        ]

        fig.add_trace(
            go.Waterfall(
                name=comp,
                orientation="v",
                measure=measures,
                x=labels,
                y=values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "#2ecc71"}},
                decreasing={"marker": {"color": "#e74c3c"}},
                totals={"marker": {"color": "#3498db"}},
                showlegend=False,
            ),
            row=1,
            col=i + 1,
        )

    fig.update_layout(
        title="DRE Bridge — Company A vs Company B (Annual)",
        yaxis_title="R$",
        height=600,
    )

    return fig


def export_figures(figs: dict, folder: str):
    """
    Export Plotly figures as HTML files.

    Args:
        figs (dict): Dictionary of {name: figure}.
        folder (str): Output directory.

    Returns:
        None
    """
    os.makedirs(folder, exist_ok=True)
    for name, fig in figs.items():
        fig.write_html(os.path.join(folder, f"{name}.html"))


if __name__ == "__main__":
    path = "data/processed/dre_metrics.parquet"
    folder = "reports/figures"

    df_pict = load_processed(path)

    fig1 = plot_margins(df_pict)
    fig2 = plot_revenue(df_pict)
    fig3 = plot_ebitda_waterfall(df_pict)

    export_figures(
        {
            "margins_over_time": fig1,
            "gross_revenue_by_month": fig2,
            "ebitda_bridge_company_a": fig3,
        },
        folder,
    )
    print("Figures exported to:", folder)