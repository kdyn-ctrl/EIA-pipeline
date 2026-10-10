# Automated EIA Weekly Petroleum Inventory Data Pipeline

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://eia-pipeline-5rxbqvmursugxhzg2vw3de.streamlit.app/)
[![Weekly Pipeline](https://github.com/kdyn-ctrl/EIA-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/kdyn-ctrl/EIA-pipeline/actions/workflows/pipeline.yml)

🌐 **Live Interactive Dashboard:** [eia-pipeline.streamlit.app](https://eia-pipeline-5rxbqvmursugxhzg2vw3de.streamlit.app/)

An automated, production-grade ETL data pipeline that extracts, validates, and stores weekly fundamental energy inventory data from the **U.S. Energy Information Administration (EIA) API v2**.

Designed with **idempotent database operations**, **defensive data validation**, and **structured production logging** for energy commodity analytics and quantitative research.

---

## 🏗️ Architecture & Data Flow

```text
       ┌───────────────────────────────┐
       │   EIA API v2 (REST Endpoint)  │
       │  Weekly Petroleum Stocks Data │
       └──────────────┬────────────────┘
                      │
                      │  HTTP GET (Authenticated, Timeout-bounded)
                      ▼
       ┌───────────────────────────────┐
       │   Raw Ingestion & Caching     │
       │       (raw_data.json)         │
       └──────────────┬────────────────┘
                      │
                      │  Defensive Validation & Type Casting
                      ▼
       ┌───────────────────────────────┐
       │   Idempotent Database Loader  │
       │    (SQLite / inventory.db)    │
       │  UNIQUE(period, product, area)│
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │   Downstream Analytics & SQL  │
       │   Regional Spreads & PADDs    │
       └───────────────────────────────┘
```

---

## ⚙️ Key Engineering Principles

1. **Idempotency ($f(f(x)) = f(x)$):**
   - In production data systems, automated jobs may retry upon transient network failures.
   - Idempotency is strictly enforced at the database level using a composite unique constraint: `UNIQUE(period, product_name, area_name)`.
   - Records are upserted via `INSERT OR REPLACE`, ensuring that re-running the pipeline produces zero duplicate rows and zero data drift.

2. **Defensive Ingestion & Edge Case Handling:**
   - Safe dictionary extraction via `.get()` prevents unhandled `KeyError` crashes when upstream API responses change schema.
   - Robust type casting (`try/except ValueError`) handles delayed reporting and null payload entries gracefully.

3. **Production Logging & Observability:**
   - Replaced unmonitored `print` statements with Python's built-in `logging` module.
   - Formatted with ISO timestamps, log severity levels (`INFO`, `WARNING`, `ERROR`), and batch volume metrics.

4. **Security & SQL Injection Prevention:**
   - Zero SQL concatenation; 100% parameterized queries using binding tuples.
   - API keys and environment configurations managed securely through `.env` and shielded from version control via `.gitignore`.

---

## 📊 Database Schema (`schema.sql`)

```sql
CREATE TABLE IF NOT EXISTS petroleum_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period DATE NOT NULL,
    product_name TEXT NOT NULL,
    area_name TEXT NOT NULL,
    inventory_barrels INTEGER NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period, product_name, area_name)
);
```

### Data Dictionary:
- **`period`**: The EIA reporting week (e.g., `2026-09-11`).
- **`product_name`**: Refined product category (e.g., `Distillate Fuel Oil`, `Gasoline Blending Components`, `Crude Oil`).
- **`area_name`**: Geographic market or Petroleum Administration for Defense District (`U.S.`, `PADD 1`, `PADD 3`, etc.).
- **`inventory_barrels`**: Volume in thousands of barrels (`MBBL`).
- **`ingested_at`**: UTC timestamp recording when the record was loaded into the database.

---

## 📈 Sample Analytical SQL Queries

### 1. Latest Total U.S. Stocks by Product Category
```sql
SELECT 
    product_name, 
    inventory_barrels AS volume_mbbl,
    period
FROM petroleum_inventory
WHERE area_name = 'U.S.'
ORDER BY inventory_barrels DESC;
```

### 2. Regional Distillate Fuel Oil Stocks Across PADDs
```sql
SELECT 
    area_name, 
    inventory_barrels AS distillate_mbbl,
    period
FROM petroleum_inventory
WHERE product_name = 'Distillate Fuel Oil' AND area_name != 'U.S.'
ORDER BY inventory_barrels DESC;
```

---

## 📊 Live Interactive Dashboard (`app.py`)

An interactive analytics web dashboard built with **Streamlit** to visualize regional supply/demand fundamentals and PADD inventory trends.

### Running Locally:
```bash
streamlit run app.py
```

### Features:
- **Top-Level KPI Cards:** Real-time national ending stocks for Crude Oil, Gasoline, and Distillates.
- **PADD Comparison Bar Chart:** Direct comparison of inventory balances across regional refining hubs (e.g. PADD 1 vs. PADD 3).
- **Searchable Table & Filter:** Interactive data grid with instant CSV export.

---

## 📁 Public Data Access (Git Scraping)
The latest weekly data is automatically exported to [`data/latest_inventory.csv`](data/latest_inventory.csv) on every scheduled pipeline run. GitHub automatically renders this as an interactive spreadsheet in your browser.

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/kdyn-ctrl/EIA-pipeline.git
cd EIA-pipeline
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate   # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Credentials
Create a `.env` file in the project root:
```env
EIA_API_KEY=your_eia_api_key_here
```
*(Get a free API key at [eia.gov/opendata](https://www.eia.gov/opendata/))*

### 4. Run the Pipeline & Dashboard
```bash
# Run automated ETL ingestion
python pipeline.py

# Launch interactive analytics dashboard
streamlit run app.py
```

### Output:
```text
2026-10-10 14:31:22 [INFO] === Starting EIA Petroleum Pipeline Run ===
2026-10-10 14:31:22 [INFO] Starting EIA data extraction...
2026-10-10 14:31:29 [INFO] Extraction successful: raw data saved to raw_data.json
2026-10-10 14:31:29 [INFO] Starting database loading into inventory.db...
2026-10-10 14:31:29 [INFO] Load complete: 50 upserted, 0 skipped.
2026-10-10 14:31:29 [INFO] === Pipeline Run Finished Successfully ===
```
