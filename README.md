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
│   └── 01_Behavioral_Insights.ipynb   # returns vs. fulfilment time / session intent
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

**1. Sales grew steadily and returns grew with sales.** GMV increased every quarter from 2025-Q1 to 2026-Q3 (roughly 100K to 280K per quarter on the dashboard). Gross margin stayed around 50% across full quarters. Return amount rose roughly in line with sales, and the overall return rate is about 15.7% for the period shown.

**2. No visible link between fulfilment time and returns.** The order-level return rate stays within about 28–30% across fulfilment-time bins from under 24 hours to over 120 hours (`plot_logistics_trend`). In this dataset, slower fulfilment is not associated with more returns. This is a descriptive comparison with no significance test and no adjustment for other factors.

**3. Session intent vs. returns: no clear difference among delivered items.** Only 9.1% of purchase sessions (16,446 of 181,466) could be matched to an order, so this covers a small subset. Among matched items, return rates are 9.8% (Impulse Buyers), 9.3% (Targeted Searchers) and 7.1% (Heavy Browsers) when all items are counted. Among delivered items, the only ones that can be returned, the rates are 28.0%, 28.9% and 25.7% (n = 4,507 / 1,407 / 739), and the approximate 95% intervals overlap. The lower all-items rate for Heavy Browsers is mostly explained by a smaller share of delivered items (28% vs 35%), not by a clear difference in return behaviour. This is an observational comparison with no adjustment for product mix, and it does not show that browsing reduces returns (see Limitation 5).

**4. Customer segments (RFM).** Potential Loyalists are the largest segment by both users and revenue, followed by At Risk (by revenue) and New Customers (by users). The segment rules are coarse (see [Limitations](#data--limitations)), so these are descriptive groupings. Whether retention campaigns aimed at At Risk customers would pay off is a hypothesis for future testing, not a result of this project.

## Data & Limitations

### Data

- **Source:** TheLook eCommerce, a fictional online clothing retailer. The data is generated by a simulator and published as the BigQuery public dataset `bigquery-public-data.thelook_ecommerce`.
- **Tables used:** `events`, `inventory_items`, `orders`, `order_items`, `users`, exported as CSV.
- **Not committed:** raw CSVs and Parquet outputs are gitignored because of their size.
- CSVs were exported with SQL queries in the BigQuery console.
### Limitations

1. **Synthetic data.** Patterns, including the "no effect" results above, reflect how the data was generated and may not hold in real business data.
2. **Descriptive, not causal.** There is no randomisation, formal hypothesis testing or adjustment for confounders. The 95% intervals shown are approximate and treat items as independent. Group differences should not be read as causal effects. `traffic_source` is an acquisition channel, not an experiment arm, and `mart_experimentation_base` is only a baseline table.
3. **Timestamp cleaning removes about 20% of order items.** Rows where a shipped, delivered or returned timestamp is earlier than `created_at` (35,889 rows found in EDA, out of roughly 182K) are dropped, because they would give negative fulfilment times. This also changes GMV and the status mix, and the effect has not been quantified yet.
4. **Return-rate figures use different definitions and are not directly comparable.** Only items that reach delivery can be returned, so rates based on delivered items are much higher than rates based on all items. The impulse mart reports both: about 7–10% of all matched items and about 26–29% of delivered items. The logistics mart (about 28–30%) is order level among delivered orders. The dashboard figure (about 15.7%) is returned items ÷ all items for the period shown, on the cleaned data (see [Metric definitions](#pipeline)).
5. **Session-to-order matching is loose.** The event data has no order key, so purchase sessions are matched to items by user and a ±30-minute window around the purchase event, keeping the closest session per item. Only 9.1% of purchase sessions (16,446 of 181,466) match an order, and the matched time gaps are spread across the window (median about 10–12 minutes) rather than clustered near zero. Results describe this matched subset only. The segment thresholds (10 / 60 minutes, 6 / 12 page views) are arbitrary.
6. **RFM is heuristic.** Scores are computed per user per quarter, so most users have a single order and frequency scores are weakly informative. "Potential Loyalists" is a broad catch-all rule, and "New Customers" is defined by recency plus one order in the quarter, not by first-order date.
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

Open `notebook/01_Behavioral_Insights.ipynb` with the `notebook/` folder as the working directory (the default in Jupyter and VS Code). It reads the marts from `../dataset/processed/` and uses the chart functions in `src/visualizations.py`:

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

- Improve session-to-order matching (current match rate 9.1%).
- Improve session-to-order matching (current match rate: 9.1%).
- Add formal significance tests (with standard errors clustered by user) and adjust for covariates such as product category, order size and customer attributes; extend confidence intervals to the other comparisons.
- Quantify the effect of the timestamp cleaning (before/after comparison of GMV and return rate).
- Look at multi-warehouse split shipments (`total_dc > 1`) as a follow-up question.
- Make the pipeline runnable from the repository root.