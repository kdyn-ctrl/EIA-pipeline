import json
import logging 
import os
import sqlite3
import requests
from dotenv import load_dotenv

# 1. Configure strucutred production logging
logging.basicConfig(
    level=logging.INFO,
    format= "%(asctime)s [%(levelname)s] %(message)s",
    datefmt= "%Y -%m -%d %H:%M:%S",
)

API_URL = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
RAW_DATA_PATH = "raw_data.json"
DB_PATH = "inventory.db" 


def extract_data() -> bool:
    """Fetch raw weekly petroleum inventory data from EIA API"""
    load_dotenv()
    api_key = os.getenv("EIA_API_KEY")

    if not api_key:
        logging.error("EIA_API_KEY enviornment variable is missing")
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
        logging.error("API request failed %s", e)
        return False
    
def load_data() -> tuple[int, int]:
    """Parse raw JSON and upsert records into SQLite database"""
    logging.info("Starting database laoding into %s...",DB_PATH)

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


def run_pipeline():
    """Master pipeline runner."""
    logging.info("=== Starting EIA Petroleum Pipleline Run ===")
    success = extract_data()
    if not success:
        logging.error("Pipeline aborted: Extraction failed.")
        return


    load_data()
    logging.info("=== Pipeline Run Finished Successfully ===")


if __name__ == "__main__":
    run_pipeline() 