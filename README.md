# 🛒 TheLook E-Commerce: End-to-End Data Engineering & BI Analytics Pipeline

## 📖 Project Overview
This project builds a robust, end-to-end Data Engineering pipeline and Business Intelligence (BI) solution for a mock e-commerce platform, "TheLook". It processes raw transactional and web traffic logs, models the data into scalable analytical tables, and extracts actionable business insights regarding financial health, user behavior, RFM segmentation, and logistics performance.

## 🛠️ Tech Stack
* **Data Processing & ETL**: Python, DuckDB
* **Data Storage**: Parquet, CSV
* **Exploratory Data Analysis (EDA)**: Jupyter Notebook, Pandas
* **Data Visualization**: Matplotlib, Seaborn
* **Business Intelligence**: Interactive BI Dashboard (Sales & RFM Analysis)

## 🗂️ Project Structure
```text
📦 project-root
 ┣ 📂 dataset
 ┃ ┣ 📂 raw                          # Raw CSV files (events, orders, users, etc.)
 ┃ ┗ 📂 processed                    # Cleaned Parquet files, OBTs, and Data Marts
 ┣ 📂 prototypes                     # Test draft 
 ┃ ┣ 📜 01_data_cleaning.ipynb       # Clean raw CSV files (events, orders, users, etc.)
 ┃ ┣ 📜 02_build_sales_obt.ipynb     # Build sale OBTs (Frontend_Traffic_OBT & Backend_Sales_OBT)
 ┃ ┗ 📜 03_data_marts_.ipynb         # Build data marts (mart_financial_summary, mart_experimentation_base, mart_impulse_penalty, etc.)
 ┣ 📂 notebooks
 ┃ ┗ 📜 01_Behavioral_Insights.ipynb # Causal inference analysis, hypothesis testing (e.g., logistics vs. returns), and behavioral data science insights.
 ┣ 📂 src
 ┃ ┣ 📜 etl_pipeline.py              # Core DuckDB ETL pipeline (Phase 1 to Phase 3)
 ┃ ┣ 📜 init.py                      # Empty file
 ┃ ┗ 📜 visualization.py             # Python visualization scripts (Seaborn/Matplotlib)
 ┣ 📂 dashboards
 ┃ ┗ 🖼️ Sales_RFM_Dashboard.png      # Final BI Dashboard replacing traditional reports
 ┗ 📜 README.md
 ┗ 📜 Requirements.txt
```

## ⚙️ Data Pipeline Architecture
The automated ETL pipeline (`src/etl_pipelines.py`) is powered by **DuckDB** for blazing-fast in-memory analytical processing. It follows a structured 3-phase Medallion-like architecture:

**Phase 1: Raw Data Cleaning**
* Ingests raw `.csv` files.
* Handles missing identities (`user_id = 0`), imputes missing metadata (`'Unknown'`), and enforces defensive timestamp casting.
* Filters out chronological anomalies (e.g., items shipped before creation) and saves outputs as compressed `.parquet` files.

**Phase 2: One Big Tables (OBTs)**
* `Frontend_Traffic_OBT`: Joins event logs with user attributes to track session journeys.
* `Backend_Sales_OBT`: Integrates inventory, order items, and user demographics into a comprehensive sales wide-table.

**Phase 3: Business Data Marts**
* Generates highly aggregated tables for downstream BI consumption:
    * `mart_financial_summary`: Quarterly GMV, Net Revenue, COGS, Margin, and Return Rates.
    * `mart_rfm_segmentation`: Quintile-based RFM scoring to classify user life-cycle stages.
    * `mart_logistics_experience`: Tracking fulfillment delays and return flags.
    * `mart_impulse_penalty`: Session duration/intent analysis versus return rates.
    * `mart_experimentation_base`: Baseline metrics for A/B testing user traffic sources.

## 📈 Key Business Insights
**1. Profitability & The Cost of Returns:**
<br>The Sales Dashboard highlights a peak GMV in 2026-Q3. However, the Gross Profit vs. Return Impact analysis reveals that aggressive sales growth triggered a massive surge in return costs, severely eroding actual profit margins.

**2. Logistics Bottlenecks:**
<br>A non-linear logistic regression model (`plot_logistic_return_probability`) proves a direct correlation between elongated fulfillment times (especially >72 hours) and skyrocketing product return probabilities.

**3. The "Impulse Penalty" Myth:**
<br>By tracking frontend session intent, the data debunks the assumption that quick, impulsive buyers return the most items. Instead, "Heavy Browsers" (long session durations, high page views) exhibit the highest return rates, indicating comparison-shopping and "wardrobing" behaviors.

**4. Targeted Customer Retention:**
<br>The RFM Segmentation tree maps demonstrate that "Potential Loyalists" and "At Risk" segments drive the majority of current revenue. Marketing efforts should immediately pivot from pure acquisition to retaining these high-value cohorts.

## 🚀 How to Run
**1. Install dependencies**:
```text
Bash
pip install -r requirements.txt
# Or install manually: pip install duckdb pandas numpy matplotlib seaborn pyarrow
```
**2. Execute the ETL Pipeline**:
<br>Ensure your raw CSV files are in `dataset/raw/.` Run the pipeline to generate all clean tables, OBTs, and Marts into `dataset/processed/`.
```text
Bash
python src/etl_pipelines.py
```
**3. Generate Visualizations**:
<br>Import and call the visualization functions in your Python environment passing the generated Data Marts:
```text
Python
from src.visualization import plot_logistics_trend, plot_impulse_penalty
# Load your parquet marts and pass them to the functions
```