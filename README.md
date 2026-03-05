# Financial Performance Analyzer — DRE Variance Analysis

This project simulates ERP-style financial transactions and processes them through a financial
reporting pipeline that reconstructs a DRE (Income Statement).

The goal is to demonstrate how transaction-level data aggregates into financial statements,
enabling analysis of gross profit, EBITDA, net income, and financial margins over time.

Synthetic transactions are generated across companies, business units, and cost centers.
Random noise is applied at the cost center level to avoid perfectly linear distributions
and better approximate real operational variability.

---

## Project Structure

```
financial-performance-analyzer/
├── data/
│   ├── raw/                  # Output of extract.py (parquet)
│   └── processed/            # Output of transform.py (parquet)
├── notebooks/                # Exploratory analysis
├── reports/
│   └── figures/              # Plotly charts (HTML)
├── scripts/
│   └── generate_data.py      # Synthetic data generator
├── sql/
│   └── 01_schema.sql         # Database schema
├── src/
│   ├── extract.py
│   ├── transform.py
│   └── visualize.py
├── .env.example
├── docker-compose.yml
└── requirements.txt
```

---

## Architecture

```
ERP-style Transactions (synthetic)
            │
            ▼
      PostgreSQL Database
            │
            ▼
      src/extract.py       →   data/raw/transactions.parquet
            │
            ▼
      src/transform.py     →   data/processed/dre_metrics.parquet
        (DRE logic)
            │
            ▼
      src/visualize.py     →   reports/figures/
```

---

## Data Source

Financial structures were inspired by real financial statements from major companies.

Dataset reference:
[Financial Statements of Major Companies 2009–2023](https://www.kaggle.com/datasets/rish59/financial-statements-of-major-companies2009-2023)

Margin proportions (gross margin, EBITDA margin, net margin) were calculated from this dataset
by industry category and used to calibrate synthetic transaction amounts. The transaction-level
detail — companies, business units, cost centers — was generated synthetically, as ERP data
is always proprietary in real environments.

---

## How to Run

**1. Clone and install dependencies**

```bash
git clone https://github.com/YOUR_USERNAME/financial-performance-analyzer.git
cd financial-performance-analyzer

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure environment**

```bash
cp .env.example .env
```

**3. Start PostgreSQL**

```bash
docker-compose up -d
```

**4. Generate synthetic data and load into Postgres**

```bash
python scripts/generate_data.py
```

**5. Run the pipeline**

```bash
python -m src.extract
python -m src.transform
python -m src.visualize
```

Charts will be saved to `reports/figures/` as interactive HTML files.

---

## Outputs

**margins_over_time**
Line chart comparing gross margin, EBITDA margin, and net margin across 12 months for both
companies. Highlights profitability trends and margin stability over time.

**gross_revenue_by_month**
Grouped bar chart showing monthly revenue for Company A and Company B side by side.
Useful for comparing revenue scale and identifying seasonality patterns.

**ebitda_bridge_company_a**
Waterfall chart decomposing how each DRE line contributes to EBITDA for Company A.

```
Receita Bruta → - Deduções → - COGS → - Opex → = EBITDA
```

This visualization mirrors how financial analysts explain profit formation in business reviews.

---

## Technical Decisions

**Amount sign convention**
Revenue is stored as positive, costs and deductions as negative. This allows financial totals
to be calculated with a plain `SUM(amount)` without conditional logic in queries.

**Parquet format**
Processed datasets are stored in Parquet, a columnar format optimized for analytical workloads.
Faster to read and significantly more compact than CSV for data pipelines.

**SQLAlchemy over psycopg2**
SQLAlchemy provides an abstraction layer with cleaner query parameterization and seamless
Pandas integration via `pd.read_sql`. Improves maintainability compared to raw psycopg2 cursors.

**YoY calculations return NaN**
Expected behavior — the dataset only covers 2023. Adding a second year of transactions would
automatically populate YoY metrics without any changes to the pipeline logic.

---

## Technologies

Python, Pandas, NumPy, PostgreSQL, SQLAlchemy, Plotly, Docker, Parquet
