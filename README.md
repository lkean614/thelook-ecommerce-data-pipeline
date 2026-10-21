# TheLook E-Commerce: End-to-End Data Pipeline & BI Analytics

A batch ETL pipeline and analytics project built on the TheLook e-commerce dataset. Raw CSV exports (events, orders, order items, inventory, users) are cleaned and modelled with Python and DuckDB into analysis-ready Parquet tables (clean tables → One Big Tables → data marts). The marts feed a sales / RFM dashboard and a few exploratory questions about returns and customer behaviour.

> **Note on the data:** TheLook is a *synthetic* dataset (see [Data & Limitations](#data--limitations)). Findings describe this dataset only, not real customers. The goal of this project is to demonstrate the workflow: data cleaning, modelling, metric design and exploratory analysis.

## Contents

- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Pipeline](#pipeline)
- [Dashboard](#dashboard)
- [Key findings](#key-findings)
- [Data & Limitations](#data--limitations)
- [How to run](#how-to-run)
- [Planned improvements](#planned-improvements)

## Tech stack

- **ETL / modelling:** Python, SQL (DuckDB)
- **Storage:** Parquet
- **EDA & charts:** pandas, matplotlib, seaborn, Jupyter
- **Dashboard:** Power BI

## Project structure

```
.
├── dataset/                       # NOT committed (gitignored)
│   ├── raw/                       # source CSV exports
│   └── processed/                 # clean tables, OBTs, data marts (Parquet)
├── src/
│   ├── __init__.py
│   ├── etl_pipeline.py            # DuckDB ETL: clean -> OBTs -> marts
│   └── visualizations.py          # seaborn / matplotlib chart functions
├── notebook/
│   ├── 01_Behavioral_Insights.ipynb   # returns vs. fulfilment time / session intent
|   └── 02_Data_Quality_Impact_Analysis.ipynb
├── prototypes/                    # exploratory versions of the cleaning, OBT and mart logic
│   ├── 01_data_cleaning.ipynb
│   ├── 02_build_sales_obt.ipynb
│   └── 03_data_marts_.ipynb
├── dashboards/
│   ├── Sales_RFM_Dashboard.png
│   └── dashboard_demo.mp4
├── requirements.txt
└── README.md
```

`src/etl_pipeline.py` is the maintained version of the pipeline; the notebooks in `prototypes/` are the step-by-step work it was built from.

## Pipeline

`src/etl_pipeline.py` runs three phases in DuckDB.

**Phase 1: clean** (`dataset/raw/*.csv` → `dataset/processed/clean_*.parquet`)

- `events`: anonymous visitors (`user_id` is NULL) are set to `0`; the string `'null'` in `city` becomes `'Unknown'`.
- `inventory_items`: missing product name / brand become `'Unknown'`.
- `users`: missing email, gender and street address become `'Unknown'`; the string `'null'` in `city` becomes `'Unknown'`.
- `orders`, `order_items`: timestamps are cast with `TRY_CAST`; rows whose timestamps are out of order (e.g. shipped before created) are dropped. See [Limitations](#data--limitations).
- Order items removed by the timestamp check are written to `exception_order_items`, so that raw = clean + exception.

**Phase 2: One Big Tables**

- `Frontend_Traffic_OBT`: one row per event, joined with user attributes.
- `Backend_Sales_OBT`: one row per inventory item, joined with order items, orders and users. Unsold items have NULL order fields, so the marts filter on `user_id IS NOT NULL`.

**Phase 3: data marts**

| Mart | Grain | Contents |
|---|---|---|
| `mart_financial_summary` | quarter | GMV, net revenue, COGS, gross profit and margin, AOV, ARPU, return rate |
| `mart_rfm_segmentation` | user × quarter (last 12 months of data) | RFM quintile scores and a rule-based segment |
| `mart_logistics_experience` | order (delivered orders only) | item count, number of distribution centres, hours from order creation to last delivery, return flag |
| `mart_experimentation_base` | identified user | acquisition channel (`traffic_source`), event count, converted flag, total spend. A baseline table for future experiments; the channel is observational, not randomised |
| `mart_impulse_penalty` | session-intent segment | return rate by session-intent segment, for sessions matched to an order (see [Limitations](#data--limitations)) |

**Metric definitions**

| Metric | Definition |
|---|---|
| GMV | Sum of `sale_price` over all items, including returned and cancelled |
| Net revenue | Sum of `sale_price` excluding returned and cancelled items |
| COGS | Cost of the same items counted in net revenue |
| Gross profit / margin | Net revenue − COGS / ÷ net revenue. Returns are already excluded from net revenue, so they do not reduce margin; they are shown separately as *Return Amount* |
| AOV | GMV ÷ distinct orders |
| ARPU | Net revenue ÷ active buyers |
| Return rate (financial mart, dashboard) | Returned items ÷ all items in the period (item level) |
| Return flag (logistics mart) | 1 if the order status is `Returned`, among orders with delivered items (order level) |
| Return rate (impulse mart) | Returned ÷ all matched items, and returned ÷ delivered (Complete + Returned) items (item level) |

## Dashboard

![Sales & RFM dashboard](dashboards/Sales_RFM_Dashboard.png)

## Key findings

These are descriptive results on a synthetic dataset. Findings 1, 2 and 4 are simple descriptive summaries; finding 3 shows approximate 95% intervals but no formal hypothesis test or adjustment for other factors.

**1. Sales grew steadily and returns grew in line with sales.** Quarterly GMV rose every quarter from about 417K in 2025-Q1 to about 1.14M in 2026-Q3 (cleaned data, which understates GMV by about 20%, see Limitation 3; 2026-Q4 is a partial quarter). Gross margin stayed at about 51–52% in every full quarter. The all-items return rate stayed between 8.2% and 9.2% per quarter (8.8% overall for 2025-Q1 to 2026-Q4), and return amount stayed at about 8–9% of GMV, so returns grew in line with sales rather than faster.

**2. No visible link between fulfilment time and returns.** The order-level return rate stays within about 28–30% across fulfilment-time bins from under 24 hours to over 120 hours (`plot_logistics_trend`). In this dataset, slower fulfilment is not associated with more returns. This is a descriptive comparison with no significance test and no adjustment for other factors.

**4. Customer segments (RFM).** For 2026-Q1 to 2026-Q3, Potential Loyalists are the largest segment (about a third of users and about 25.7% of revenue, net of returned and cancelled items), followed by Loyalists, At Risk and the catch-all "Others" segment. Champions and Cant Lose Them together are about 14% of users but about 27.5% of revenue. The segment rules are coarse (see Limitation 6), so these are descriptive groupings. Whether retention campaigns aimed at At Risk customers would pay off is a hypothesis for future testing, not a result of this project.

**4. Customer segments (RFM).** Potential Loyalists are the largest segment by both users and revenue, followed by At Risk (by revenue) and New Customers (by users). The segment rules are coarse (see [Limitations](#data--limitations)), so these are descriptive groupings. Whether retention campaigns aimed at At Risk customers would pay off is a hypothesis for future testing, not a result of this project.

## Data & Limitations

### Data

- **Source:** TheLook eCommerce, a fictional online clothing retailer. The data is generated by a simulator and published as the BigQuery public dataset `bigquery-public-data.thelook_ecommerce`.
- **Tables used:** `events`, `inventory_items`, `orders`, `order_items`, `users`, exported as CSV.
- **Not committed:** raw CSVs and Parquet outputs are gitignored because of their size.
- **Export:** CSVs were exported with SQL queries in the BigQuery console.

### Limitations

1. **Synthetic data.** Patterns, including the "no effect" results above, reflect how the data was generated and may not hold in real business data.
2. **Descriptive, not causal.** There is no randomisation, formal hypothesis testing or adjustment for confounders. The 95% intervals shown are approximate and treat items as independent. Group differences should not be read as causal effects. `traffic_source` is an acquisition channel, not an experiment arm, and `mart_experimentation_base` is only a baseline table.
3. **Timestamp cleaning removes 19.8% of order items.** 35,889 of 181,466 order items (145,577 kept) are dropped because a shipped, delivered or returned timestamp is earlier than the item's `created_at`, which would give negative fulfilment times. The rule only hits items that have shipped: about 30% of Shipped, Complete and Returned items are dropped, and no Processing or Cancelled items are, so Processing and Cancelled items rise from 35% to 44% of the cleaned data. Compared with the raw data, the cleaned data understates GMV by 19.7% and net revenue by 22.1%, and the all-items return rate falls from 10.1% to 8.8%. The return rate among delivered items is essentially unchanged (28.8% raw vs 28.7% cleaned) because Complete and Returned items are dropped at almost the same rate (30.2% vs 30.4%). 20,557 orders (16.4%) lose at least one item: 7,852 are removed entirely and 12,705 keep only some of their items, so AOV (86.25 raw vs 73.91 cleaned) and items per order (1.45 vs 1.24) are each understated by about 14%. See `notebook/02_Data_Quality_Impact_Analysis.ipynb`.
4. **Return-rate figures use different denominators.** Only items that reach delivery can be returned, so rates based on delivered items (about 26–29% in the impulse mart, about 28–30% at order level in the logistics mart) are much higher than rates based on all items (about 7–10% in the impulse mart, and 8.2–9.2% per quarter in the financial mart and dashboard, which use the cleaned data; the raw all-items rate is 10.1%, see Limitation 3). See [Metric definitions](#pipeline).
5. **Session-to-order matching is loose.** The event data has no order key, so purchase sessions are matched to items by user and a ±30-minute window around the purchase event, keeping the closest session per item. Only 9.1% of purchase sessions (16,446 of 181,466) match an order, and the matched time gaps are spread across the window (median about 10–12 minutes) rather than clustered near zero. Results describe this matched subset only. The segment thresholds (10 / 60 minutes, 6 / 12 page views) are arbitrary.
6. **RFM is heuristic.** Scores are computed per user per quarter, so most users have a single order and frequency scores are weakly informative. "Potential Loyalists" and the final "Others" segment are broad catch-all rules, and "New Customers" is defined by recency plus one order in the quarter, not by first-order date. Cancelled and returned items are excluded from the monetary value.
7. **Incomplete latest quarter.** The final quarter in the snapshot is partial.
8. **Anonymous traffic.** In the EDA snapshot, about 46% of events (roughly 1.1M of 2.4M) have no `user_id`. They are mapped to `0` and excluded from user-level marts such as `mart_experimentation_base`.

## How to run

Requires Python 3.9 or later.

**1. Install dependencies**

```bash
git clone https://github.com/lkean614/thelook-ecommerce-data-pipeline.git
cd thelook-ecommerce-data-pipeline
pip install -r requirements.txt
```

To open the notebooks you also need Jupyter (`pip install jupyter`) or VS Code's notebook support.

**2. Add the data**

Create `dataset/raw/` and `dataset/processed/`, then put these five CSV files in `dataset/raw/`:

```
events.csv   inventory_items.csv   orders.csv   order_items.csv   users.csv
```

**3. Run the ETL pipeline**

The pipeline uses paths relative to `src/`, so run it from there:

```bash
cd src
python etl_pipeline.py
```

This writes the clean tables, the two OBTs and the five marts to `dataset/processed/` and prints row counts for each step.

**4. Explore the results**

- Open `notebook/01_Behavioral_Insights.ipynb` with the `notebook/` folder as the working directory (the default in Jupyter and VS Code). It reads the marts from `../dataset/processed/` and uses the chart functions in `src/visualizations.py`:
- Open `notebook/02_Data_Quality_Impact_Analysis.ipynb` with the `notebook/` folder as the working directory (the default in Jupyter and VS Code). It reads the marts from `../dataset/processed/`

```python
import os, sys
sys.path.append(os.path.abspath('../src'))

import pandas as pd
import visualizations as vis

df_logistics = pd.read_parquet('../dataset/processed/mart_logistics_experience.parquet')
vis.plot_logistics_trend(df_logistics)
```

The notebooks in `prototypes/` also use `../dataset/...` paths and need the same folder layout.

## Planned improvements

- Improve session-to-order matching (current match rate: 9.1%).
- Add formal significance tests (with standard errors clustered by user) and adjust for covariates such as product category, order size and customer attributes; extend confidence intervals to the other comparisons.
- Quantify the effect of the timestamp cleaning (before/after comparison of GMV and return rate).
- Look at multi-warehouse split shipments (`total_dc > 1`) as a follow-up question.
- Make the pipeline runnable from the repository root.
- Keep order items with inconsistent timestamps and flag them instead of dropping them, so only the fulfilment-time analysis excludes them (the current cleaning understates GMV by about 20% and AOV by about 14%).