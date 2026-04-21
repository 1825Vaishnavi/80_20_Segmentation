import pandas as pd
import numpy as np
import sqlite3

# ── LOAD ────────────────────────────────────────────────
df = pd.read_csv("../data/raw_transactions.csv", parse_dates=["date"])
print(f"Loaded: {df.shape}")

# ══════════════════════════════════════════════════════
# STEP 2A — DATA CLEANING
# ══════════════════════════════════════════════════════

# 1. Fill missing quantity with median (safe for skewed data)
median_qty = df["quantity"].median()
df["quantity"].fillna(median_qty, inplace=True)

# 2. Fill missing region with "Unknown"
df["region"].fillna("Unknown", inplace=True)

# 3. Recalculate revenue where quantity was missing
df["revenue"] = df["quantity"] * df["unit_price"]

# 4. Drop duplicates (just in case)
before = len(df)
df.drop_duplicates(subset="transaction_id", inplace=True)
print(f"Dropped {before - len(df)} duplicates")

# 5. Add product category column
category_map = {
    "PROD_A": "Industrial Equipment",
    "PROD_B": "Consumables",
    "PROD_C": "Specialty Chemicals",
    "PROD_D": "Safety Supplies",
    "PROD_E": "Precision Instruments",
}
df["product_category"] = df["product_id"].map(category_map)

print("✅  Cleaning done")
print(df.isnull().sum())

# ══════════════════════════════════════════════════════
# STEP 2B — LOAD INTO SQLite & RUN 80/20 ANALYSIS
# ══════════════════════════════════════════════════════

conn = sqlite3.connect("../data/transactions.db")
df.to_sql("transactions", conn, if_exists="replace", index=False)

# ── Customer-level revenue aggregation ──────────────────
customer_revenue_sql = """
SELECT
    customer_id,
    COUNT(transaction_id)            AS total_orders,
    ROUND(SUM(revenue), 2)           AS total_revenue,
    ROUND(AVG(unit_price), 2)        AS avg_unit_price,
    ROUND(AVG(quantity), 2)          AS avg_quantity
FROM transactions
GROUP BY customer_id
ORDER BY total_revenue DESC
"""
cust_df = pd.read_sql(customer_revenue_sql, conn)

# ── Pareto (80/20) Segmentation ─────────────────────────
total_rev = cust_df["total_revenue"].sum()
cust_df["cumulative_revenue"]    = cust_df["total_revenue"].cumsum()
cust_df["cumulative_revenue_pct"] = cust_df["cumulative_revenue"] / total_rev * 100
cust_df["cumulative_customer_pct"] = (
    (cust_df.index + 1) / len(cust_df) * 100
)

# Tag segments
def assign_segment(row):
    if row["cumulative_revenue_pct"] <= 50:
        return "Tier 1 – Top"       # top revenue drivers
    elif row["cumulative_revenue_pct"] <= 78:
        return "Tier 2 – Core"
    elif row["cumulative_revenue_pct"] <= 95:
        return "Tier 3 – Growth"
    else:
        return "Tier 4 – Tail"

cust_df["segment"] = cust_df.apply(assign_segment, axis=1)

# Print 80/20 finding
top20_cutoff = int(len(cust_df) * 0.20)
top20_rev    = cust_df.iloc[:top20_cutoff]["total_revenue"].sum()
top20_pct    = round(top20_rev / total_rev * 100, 1)
print(f"\n📊  TOP 20% of customers ({top20_cutoff}) drive {top20_pct}% of revenue")

# ── Save customer segment table back to DB ───────────────
cust_df.to_sql("customer_segments", conn, if_exists="replace", index=False)
cust_df.to_csv("../data/customer_segments.csv", index=False)

# ── Product-level summary ────────────────────────────────
product_sql = """
SELECT
    product_id,
    product_category,
    COUNT(transaction_id)   AS total_orders,
    ROUND(SUM(revenue), 2)  AS total_revenue,
    ROUND(AVG(unit_price), 2) AS avg_price
FROM transactions
GROUP BY product_id
ORDER BY total_revenue DESC
"""
prod_df = pd.read_sql(product_sql, conn)
prod_df.to_csv("../data/product_summary.csv", index=False)

conn.close()
print("\n✅  Segmentation done — files saved:")
print("    customer_segments.csv")
print("    product_summary.csv")
print(cust_df[["customer_id","total_revenue","segment"]].head(10))

conn.close()
