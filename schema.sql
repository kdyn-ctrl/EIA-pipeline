CREATE TABLE IF NOT EXISTS petroleum_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period DATE NOT NULL,
    product_name TEXT NOT NULL,
    area_name TEXT NOT NULL,
    inventory_barrels INTEGER NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period, product_name,area_name)

);