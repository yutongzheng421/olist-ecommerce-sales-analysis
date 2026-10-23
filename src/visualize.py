# Run the SQL in sql/ and save the charts to figures/.

import argparse
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save figures without a display

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", palette="muted")

FIGURES_DIR = Path("figures")

# (file, query names in that order)
SQL_FILES = [
    (Path("sql/01_sales_analysis.sql"), ["monthly_sales"]),
    (Path("sql/02_category_analysis.sql"), ["top_categories"]),
    (Path("sql/03_customer_behavior.sql"), ["purchase_frequency", "repurchase_rate"]),
]


def parse_sql_file(path):
    # strip -- comments first, so a ';' inside a comment can't split a query
    text = path.read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("--")]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]


def plot_monthly_sales(df, out_path):
    data = df.copy()
    data["order_month"] = pd.to_datetime(data["order_month"])

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(data["order_month"], data["total_sales"],
             marker="o", linewidth=2, color="tab:blue", label="Revenue (BRL)")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Item Sales (BRL, freight excl.)")
    ax1.ticklabel_format(axis="y", style="plain")

    ax2 = ax1.twinx()
    ax2.plot(data["order_month"], data["order_count"],
             marker="s", linewidth=1.5, color="tab:orange", label="Order count")
    ax2.set_ylabel("Order Count")
    ax2.ticklabel_format(axis="y", style="plain")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")

    ax1.set_title("Monthly Sales Trend")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_top_categories(df, out_path):
    data = df.sort_values("total_sales")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(data["category"], data["total_sales"])
    ax.set_title("Top 10 Product Categories by Sales")
    ax.set_xlabel("Item Sales (BRL, freight excl.)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_purchase_frequency(df, out_path):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df["order_count"].astype(str), df["customer_count"])
    ax.set_title("Customer Purchase Frequency")
    ax.set_xlabel("Orders per Customer")
    ax.set_ylabel("Number of Customers")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=None)
    args = parser.parse_args()

    if args.db is None:
        args.db = Path("data/olist_clean.db")
        if not args.db.exists():
            args.db = Path("data/olist.db")
    if not args.db.exists():
        print(f"Database not found: {args.db}. Run load_data.py and clean_data.py first.")
        return

    queries = {}
    for sql_file, names in SQL_FILES:
        statements = parse_sql_file(sql_file)
        if len(statements) != len(names):
            print(f"{sql_file}: expected {len(names)} queries, found {len(statements)}")
            return
        for i, name in enumerate(names):
            queries[name] = statements[i]

    conn = sqlite3.connect(args.db)
    results = {name: pd.read_sql_query(stmt, conn) for name, stmt in queries.items()}
    conn.close()

    FIGURES_DIR.mkdir(exist_ok=True)

    plot_monthly_sales(results["monthly_sales"], FIGURES_DIR / "monthly_sales_trend.png")
    plot_top_categories(results["top_categories"], FIGURES_DIR / "top_categories.png")
    plot_purchase_frequency(results["purchase_frequency"], FIGURES_DIR / "purchase_frequency.png")

    rr = results["repurchase_rate"].iloc[0]
    print("Repurchase rate:")
    print(f"  Total customers:    {int(rr['total_customers']):,}")
    print(f"  Repeat customers:   {int(rr['repeat_customers']):,}")
    print(f"  Repurchase rate:    {rr['repurchase_rate_pct']:.2f}%")

    monthly = results["monthly_sales"]
    top = results["top_categories"].iloc[0]
    print(f"\nMonthly sales range: {monthly['total_sales'].min():,.0f} ~ "
          f"{monthly['total_sales'].max():,.0f} BRL")
    print(f"Top category:        {top['category']} ({top['total_sales']:,.0f} BRL)")

    print(f"\nCharts saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
