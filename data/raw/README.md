# data/raw

This directory holds the raw CSV files (not committed to GitHub — excluded by the root `.gitignore`).

## Source

Olist Brazilian E-Commerce Dataset:
<https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>

## Required Files

Place the following 9 CSVs here, or point `src/load_data.py` at their location with `--data-dir`:

- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `product_category_name_translation.csv`
