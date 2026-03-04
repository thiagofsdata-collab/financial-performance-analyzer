import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def load_processed(path):
    df = pd.read_parquet(path)
    return df

def plot_margins(df):
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
    company_a = df[df["company"] == "Company A"].sum(numeric_only=True)

    fig = go.Figure(go.Waterfall(
        name="EBITDA Bridge",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Receita Bruta", "Deducoes da Receita", "COGS", "Opex", "EBITDA"],
        y=[
            company_a["Receita Bruta"],
            company_a["Deducoes da Receita"],
            company_a["COGS"],
            company_a["Opex"],
            company_a["EBITDA"],
        ],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    fig.update_layout(title="EBITDA Bridge — Company A (Annual)")
    return fig


def export_figures(figs: dict, folder: str):
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