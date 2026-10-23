# Import the Olist CSVs into a SQLite database.

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

TABLES = {
    "olist_customers_dataset.csv": "olist_customers",
    "olist_geolocation_dataset.csv": "olist_geolocation",
    "olist_order_items_dataset.csv": "olist_order_items",
    "olist_order_payments_dataset.csv": "olist_order_payments",
    "olist_order_reviews_dataset.csv": "olist_order_reviews",
    "olist_orders_dataset.csv": "olist_orders",
    "olist_products_dataset.csv": "olist_products",
    "olist_sellers_dataset.csv": "olist_sellers",
    "product_category_name_translation.csv": "product_category_name_translation",
}


def load_table(conn, csv_path):
    # utf-8-sig removes the BOM that some files carry
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df.columns = [c.strip().strip('"') for c in df.columns]
    table = TABLES[csv_path.name]
    df.to_sql(table, conn, if_exists="replace", index=False)
    return table, len(df)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--db", type=Path, default=Path("data/olist.db"))
    args = parser.parse_args()

    missing = [f for f in TABLES if not (args.data_dir / f).exists()]
    if missing:
        print("Missing files in --data-dir:")
        for f in missing:
            print("  -", f)
        return

    args.db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    for filename in TABLES:
        table, rows = load_table(conn, args.data_dir / filename)
        print(f"Imported {table:<35} {rows:>8,} rows")
    conn.close()

    print(f"\nDone! Database: {args.db}")


if __name__ == "__main__":
    main()
