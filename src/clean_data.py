# Clean the raw tables: data/olist.db -> data/olist_clean.db.

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

KEYS = {
    "olist_customers": ["customer_id"],
    "olist_geolocation": None,
    "olist_order_items": ["order_id", "order_item_id"],
    "olist_order_payments": ["order_id", "payment_sequential"],
    "olist_order_reviews": ["review_id"],
    "olist_orders": ["order_id"],
    "olist_products": ["product_id"],
    "olist_sellers": ["seller_id"],
    "product_category_name_translation": ["product_category_name"],
}

TIMESTAMP_COLS = {
    "olist_orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_items": ["shipping_limit_date"],
    "olist_order_reviews": ["review_creation_date", "review_answer_timestamp"],
}


def normalize_timestamps(series):
    dt = pd.to_datetime(series, errors="coerce")
    result = dt.dt.strftime("%Y-%m-%d %H:%M:%S")
    return result.where(dt.notna(), None)


def clean_table(name, df):
    before = len(df)
    note = ""

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    for col in TIMESTAMP_COLS.get(name, []):
        df[col] = normalize_timestamps(df[col])

    keys = KEYS.get(name)
    if keys:
        df = df.drop_duplicates(subset=keys, keep="first")
    else:
        df = df.drop_duplicates()

    if name == "olist_products":
        n_null = int(df["product_category_name"].isna().sum())
        df["product_category_name"] = df["product_category_name"].fillna("unknown")
        if n_null:
            note = f"filled {n_null:,} null category names"
    elif name == "olist_orders":
        df = df.dropna(subset=["order_purchase_timestamp"])
    elif name == "olist_order_items":
        df = df[df["price"].notna() & (df["price"] >= 0)
                & df["freight_value"].notna() & (df["freight_value"] >= 0)]
    elif name == "olist_order_payments":
        df = df[df["payment_value"].notna() & (df["payment_value"] >= 0)]

    return df, before - len(df), note


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/olist.db"))
    parser.add_argument("--out", type=Path, default=Path("data/olist_clean.db"))
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Raw database not found: {args.db}. Run load_data.py first.")
        return

    conn = sqlite3.connect(args.db)
    out_conn = sqlite3.connect(args.out)

    total_removed = 0
    for name in KEYS:
        df = pd.read_sql_query(f"SELECT * FROM {name}", conn)
        before = len(df)
        df, removed, note = clean_table(name, df)
        df.to_sql(name, out_conn, if_exists="replace", index=False)
        total_removed += removed
        suffix = f"  ({note})" if note else ""
        print(f"{name:<35} {before:>8,} -> {len(df):>8,}  (removed {removed:,}){suffix}")

    conn.close()
    out_conn.close()

    print(f"\nTotal rows removed: {total_removed:,}")
    print(f"Done! Clean database: {args.out}")


if __name__ == "__main__":
    main()
