import csv
import json
import logging 
import os
import sqlite3
import requests
from dotenv import load_dotenv

# 1. Configure structured production logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

API_URL = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
RAW_DATA_PATH = "raw_data.json"
DB_PATH = "inventory.db"
CSV_PATH = "data/latest_inventory.csv"


def extract_data() -> bool:
    """Fetch raw weekly petroleum inventory data from EIA API."""
    load_dotenv()
    api_key = os.getenv("EIA_API_KEY")

    if not api_key:
        logging.error("EIA_API_KEY environment variable is missing.")
        return False

    params = {
        "api_key": api_key,
        "frequency": "weekly",
        "data[0]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 50,
    }

    logging.info("Starting EIA data extraction...")
    try: 
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
 
        with open(RAW_DATA_PATH, "w") as f:
            json.dump(response.json(), f, indent=4)
        
        logging.info("Extraction successful: raw data saved to %s", RAW_DATA_PATH)
        return True
    
    except requests.RequestException as e:
        logging.error("API request failed: %s", e)
        return False
    

def load_data() -> tuple[int, int]:
    """Parse raw JSON and upsert records into SQLite database."""
    logging.info("Starting database loading into %s...", DB_PATH)

    with open(RAW_DATA_PATH, "r") as f:
        payload = json.load(f)

    records = payload.get("response", {}).get("data", [])
    inserted_count = 0
    skipped_count = 0

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for record in records:
            period = record.get("period")
            product = record.get("product-name")
            area = record.get("area-name")
            raw_value = record.get("value")

            if not period or not product or not area or raw_value is None:
                skipped_count += 1
                continue

            try:
                barrels = int(raw_value)
            except ValueError:
                skipped_count += 1
                continue

            cursor.execute(
                """
                INSERT OR REPLACE INTO petroleum_inventory 
                (period, product_name, area_name, inventory_barrels)
                VALUES (?, ?, ?, ?)
                """,
                (period, product, area, barrels),
            )
            inserted_count += 1

        conn.commit()

    logging.info("Load complete: %d upserted, %d skipped.", inserted_count, skipped_count)
    return inserted_count, skipped_count


def export_to_csv(csv_path: str = CSV_PATH) -> bool:
    """Export database records to a public CSV for GitHub visual rendering."""
    logging.info("Exporting database records to %s...", csv_path)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT period, product_name, area_name, inventory_barrels, ingested_at
            FROM petroleum_inventory
            ORDER BY period DESC, product_name ASC, area_name ASC
            """
        )
        rows = cursor.fetchall()
        headers = [col[0] for col in cursor.description]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    logging.info("Export complete: %d records written to %s", len(rows), csv_path)
    return True


def run_pipeline():
    """Master pipeline runner."""
    logging.info("=== Starting EIA Petroleum Pipeline Run ===")
    success = extract_data()
    if not success:
        logging.error("Pipeline aborted: Extraction failed.")
        return

    load_data()
    export_to_csv()
    logging.info("=== Pipeline Run Finished Successfully ===")


if __name__ == "__main__":
    run_pipeline()