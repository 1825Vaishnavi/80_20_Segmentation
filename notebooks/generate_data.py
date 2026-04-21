import pandas as pd
import numpy as np
import sqlite3

np.random.seed(42)

# ── CONFIG ──────────────────────────────────────────────
N = 80_000

# ── CUSTOMERS ───────────────────────────────────────────
# 500 customers; top ~100 are "heavy" buyers (80/20 effect baked in)
n_customers = 500
customer_ids = [f"CUST_{str(i).zfill(4)}" for i in range(1, n_customers + 1)]

# Assign each customer a latent "size" weight — Pareto-distributed
# so a small group naturally drives most revenue
customer_weights = np.random.pareto(a=1.0, size=n_customers) + 1
customer_weights /= customer_weights.sum()

# ── PRODUCTS ────────────────────────────────────────────
products = {
    "PROD_A": {"base_price": 120, "category": "Industrial Equipment"},
    "PROD_B": {"base_price": 45,  "category": "Consumables"},
    "PROD_C": {"base_price": 200, "category": "Specialty Chemicals"},
    "PROD_D": {"base_price": 75,  "category": "Safety Supplies"},
    "PROD_E": {"base_price": 300, "category": "Precision Instruments"},
}
product_ids   = list(products.keys())
product_prices = [products[p]["base_price"] for p in product_ids]

# ── GENERATE TRANSACTIONS ───────────────────────────────
transaction_ids = [f"TXN_{str(i).zfill(6)}" for i in range(1, N + 1)]

chosen_customers = np.random.choice(customer_ids, size=N, p=customer_weights)
chosen_products  = np.random.choice(product_ids,  size=N)

quantities = np.random.randint(1, 50, size=N)

# Price = base price ± noise (some customers get discounts)
base_prices = np.array([products[p]["base_price"] for p in chosen_products], dtype=float)
price_noise = np.random.uniform(0.85, 1.15, size=N)
unit_prices  = np.round(base_prices * price_noise, 2)

revenue = np.round(quantities * unit_prices, 2)

# Dates spread across 2 years
dates = pd.date_range("2023-01-01", "2024-12-31", periods=N)
np.random.shuffle(dates.values)   # randomise order

# Regions
regions = np.random.choice(["Northeast", "Southeast", "Midwest", "West", "Southwest"], size=N)

# Introduce ~3 % missing values in region & quantity (realistic messiness)
missing_mask_region = np.random.rand(N) < 0.03
missing_mask_qty    = np.random.rand(N) < 0.03
regions_series = pd.array(regions, dtype=object)
regions_series[missing_mask_region] = None

qty_series = quantities.astype(float)
qty_series[missing_mask_qty] = np.nan

df = pd.DataFrame({
    "transaction_id": transaction_ids,
    "customer_id":    chosen_customers,
    "product_id":     chosen_products,
    "quantity":       qty_series,
    "unit_price":     unit_prices,
    "revenue":        revenue,
    "date":           dates,
    "region":         regions_series,
})

# ── SAVE ────────────────────────────────────────────────
df.to_csv("raw_transactions.csv", index=False)
print(f"✅  Saved raw_transactions.csv  |  shape: {df.shape}")
print(f"    Missing qty rows   : {df['quantity'].isna().sum()}")
print(f"    Missing region rows: {df['region'].isna().sum()}")
print(df.head(3))