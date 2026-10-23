# E-commerce Sales Analysis (Olist Brazilian E-Commerce)

A sales analysis project built on the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce): import the CSVs into SQLite, clean the data, run aggregations with SQL, and generate charts with Python.

## Analysis Goals

1. **Monthly sales** — monthly revenue and order counts to observe the sales trend;
2. **Product category ranking** — top 10 categories by revenue;
3. **Customer purchase frequency** — distribution of customers by number of orders;
4. **Repurchase rate** — share of customers with more than one order.

## Dataset

Source: Olist Brazilian E-Commerce Dataset (Kaggle). The raw data consists of 9 CSV files, imported into same-named SQLite tables:

| Table | Description |
| --- | --- |
| `olist_orders` | Orders (purchase timestamp, status, etc.) |
| `olist_order_items` | Order line items (product, price, freight) |
| `olist_products` | Products (including category) |
| `olist_customers` | Customers |
| `olist_sellers` | Sellers |
| `olist_order_payments` | Payments |
| `olist_order_reviews` | Reviews |
| `olist_geolocation` | Geolocation (large; not used in this analysis) |
| `product_category_name_translation` | Product category Portuguese → English |

> The data is **not** committed to GitHub (excluded via `.gitignore`). Prepare the CSVs locally before running the import script.

## Project Structure

```
ecommerce-sales-analysis/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .gitignore                # Excludes data, database, charts, etc.
├── data/
│   └── raw/                  # Raw CSVs (not committed; contains a note only)
│       └── README.md
├── sql/
│   ├── 01_sales_analysis.sql # Monthly sales trend query
│   ├── 02_category_analysis.sql # Top categories query
│   └── 03_customer_behavior.sql # Purchase frequency & repurchase rate
└── src/
    ├── load_data.py          # Import CSVs into SQLite
    ├── clean_data.py         # Clean the raw tables (dedupe, nulls, types)
    └── visualize.py          # Run SQL and generate charts
```

## Setup

Requires Python 3.9+. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. **Import the data** (writes CSVs into `data/olist.db`):

   ```bash
   # If the data is under data/raw/ in this project:
   python src/load_data.py

   # If the data lives elsewhere (e.g. on the Desktop), point to it:
   python src/load_data.py --data-dir ~/Desktop/olist_data
   ```

2. **Clean the data** (writes `data/olist_clean.db`):

   ```bash
   python src/clean_data.py
   ```

3. **Generate charts** (reads `data/olist_clean.db`, writes charts to `figures/`):

   ```bash
   python src/visualize.py
   ```

## Output

`visualize.py` produces 3 charts under `figures/` and prints the repurchase rate to the console:

- `monthly_sales_trend.png` — monthly sales trend (revenue + order count, dual-axis line chart)
- `top_categories.png` — top 10 categories by sales (horizontal bar chart)
- `purchase_frequency.png` — customer purchase frequency distribution (bar chart)
- Console output — total customers, repeat customers, repurchase rate

## Metric Details

Unless noted otherwise, every metric below counts only `order_status = 'delivered'` orders, and customer-level metrics use `customer_unique_id`.

### 1. Monthly Sales

- **Definition** — per calendar month (from `order_purchase_timestamp`), the sum of item `price` across delivered orders; `order_count` is the number of distinct delivered orders in that month.
- **Tables & fields** — `olist_orders` (`order_id`, `order_status`, `order_purchase_timestamp`), `olist_order_items` (`order_id`, `price`).
- **Query logic** — join orders ↔ order items on `order_id`; keep `order_status = 'delivered'` with a non-null purchase timestamp; `GROUP BY strftime('%Y-%m', order_purchase_timestamp)`; order by month.
- **Result** — 23 months (2016-09 → 2018-08), BRL 13,221,498.11 total delivered revenue; peak month 2017-11 (BRL 987,765.37); the first months (2016-09/11/12) are nearly empty.
- **Limitations** — only delivered orders are counted, so revenue from orders still in flight is excluded and the tail of the series is understated; `price` excludes freight and returns; the earliest months are partial because the dataset starts mid-window.

### 2. Product Category Ranking (Top 10)

- **Definition** — sum of item `price` grouped by product category (English name from the translation table, falling back to the Portuguese name), delivered orders only, ranked top 10.
- **Tables & fields** — `olist_order_items` (`product_id`, `price`, `order_id`), `olist_products` (`product_id`, `product_category_name`), `product_category_name_translation` (`product_category_name`, `product_category_name_english`), `olist_orders` (`order_status`).
- **Query logic** — join items → products → translation (LEFT JOIN, so untranslated names survive); `COALESCE` the English name; filter to delivered; `GROUP BY category`; order by total sales descending; `LIMIT 10`.
- **Result** — `health_beauty` is #1 (BRL 1,233,131.72), followed by `watches_gifts` (BRL 1,166,176.98) and `bed_bath_table` (BRL 1,023,434.76).
- **Limitations** — revenue is item `price` only (no freight, no net-of-returns); categories are seller-provided and can overlap. Additionally, 610 products have missing category labels, accounting for 1,537 delivered order-item records and BRL 170,726.63 in item sales; these records are grouped under `unknown` (which ranks 21st among categories by sales), so their revenue is excluded from individual known-category totals, potentially affecting the completeness of category-level comparisons.

### 3. Customer Purchase Frequency

- **Definition** — number of delivered orders per unique customer (`customer_unique_id`), then the count of customers in each order-count bucket (1, 2, 3, …).
- **Tables & fields** — `olist_orders` (`order_id`, `customer_id`, `order_status`), `olist_customers` (`customer_id`, `customer_unique_id`).
- **Query logic** — join orders → customers on `customer_id`; filter to delivered; group by `customer_unique_id` counting distinct `order_id`; then an outer `GROUP BY order_count`.
- **Result** — 90,557 customers made 1 order, 2,573 made 2, 181 made 3, with a long tail up to 15 orders.
- **Limitations** — only delivered orders count as purchases; `customer_unique_id` is Olist's best-effort de-duplication, so a real repeat buyer who used different accounts/guest checkouts may still be split, undercounting frequency.

### 4. Repurchase Rate

- **Definition** — share of unique customers (`customer_unique_id`) with more than one delivered order.
- **Tables & fields** — `olist_orders` (`order_id`, `customer_id`, `order_status`), `olist_customers` (`customer_id`, `customer_unique_id`).
- **Query logic** — a CTE computes each customer's delivered order count; then `repeat_customers / total_customers`.
- **Result** — 3.00% (2,801 repeat customers out of 93,358).
- **Limitations** — The dataset ends in August 2018, leaving customers who purchased near the end of the observation window less time to make repeat purchases. As a result, the observed 3.00% repurchase rate may understate longer-term repeat-purchase behavior. The metric also depends on Olist's `customer_unique_id` matching and counts only delivered orders.

## Notes & Conventions

- Revenue, category ranking, purchase frequency, and repurchase rate only count `order_status = 'delivered'` orders.
- Repurchase rate / purchase frequency are measured by `customer_unique_id` (the real customer), since one real customer can have multiple `customer_id`s.

## Data Cleaning

`src/clean_data.py` turns `data/olist.db` into `data/olist_clean.db`. Rules are applied per table:

| Table | Rule | Rows affected |
| --- | --- | --- |
| all tables | trim whitespace in string columns; normalize timestamps to `YYYY-MM-DD HH:MM:SS` (unparseable → NULL) | — |
| all tables | deduplicate on natural keys | 814 (reviews) + 261,831 (geolocation); others 0 |
| `olist_products` | fill missing `product_category_name` with `unknown` | 610 filled |
| `olist_orders` | drop rows with a missing `order_purchase_timestamp` | 0 |
| `olist_order_items` | drop rows with missing/negative `price` or `freight_value` | 0 |
| `olist_order_payments` | drop rows with missing/negative `payment_value` | 0 |

The three `0` counts mean those guards are defensive only for this snapshot — no revenue-affecting rows are actually removed.
