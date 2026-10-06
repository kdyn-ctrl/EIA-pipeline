import json
import sqlite3

# 1. Load raw data from disk
with open("raw_data.json", "r") as f:
    payload = json.load(f)

records = payload.get("response", {}).get("data", [])

inserted_count = 0
skipped_count = 0

# 2. Connect to database and load records
with sqlite3.connect("inventory.db") as conn:
    cursor = conn.cursor()

    for record in records: 
        period = record.get("period")
        product = record.get ("product-name")
        area = record.get ("area-name")
        raw_value = record.get("value")

        # Check and ensure all required fields exist
        if not period or not product or not area or raw_value is None:
            skipped_count += 1
            continue


        # Safely convert string volume to integer    
        try:
            barrels = int(raw_value)
        except ValueError:
            skipped_count += 1 
            continue 

        cursor.execute(
            """
            INSERT OR REPLACE INTO petroleum_inventory
            (period, product_name, area_name, 
inventory_barrels)
            VALUES (?, ?, ?, ?)
            """,
        (period, product, area, barrels)
        )
        inserted_count += 1
        

    conn.commit()


print(f"Done: {inserted_count} records inserted/updated,{skipped_count} skipped.")