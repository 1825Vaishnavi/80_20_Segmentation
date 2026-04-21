import pandas as pd
import numpy as np
import sqlite3
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from scipy import stats

# ── LOAD ────────────────────────────────────────────────
conn = sqlite3.connect("../data/transactions.db")

df = pd.read_sql("SELECT * FROM transactions", conn)
cust_df = pd.read_sql("SELECT * FROM customer_segments", conn)
conn.close()

# ══════════════════════════════════════════════════════
# STEP 3A — ASSIGN PRICING TIERS
# ══════════════════════════════════════════════════════
# Pricing tier = which bucket the avg unit_price falls into (per customer)
# Tier A = premium, B = standard, C = discounted

cust_df["score"] = (
    0.5 * (cust_df["total_revenue"] / cust_df["total_revenue"].max()) +
    0.3 * (cust_df["total_orders"] / cust_df["total_orders"].max()) +
    0.2 * (cust_df["avg_quantity"] / cust_df["avg_quantity"].max())
)
cust_df["pricing_tier"] = pd.qcut(
    cust_df["score"],
    q=3,
    labels=["C – Discounted", "B – Standard", "A – Premium"]
)
print("Pricing tier distribution:")
print(cust_df["pricing_tier"].value_counts())

# ══════════════════════════════════════════════════════
# STEP 3B — REGRESSION MODEL (Logistic — multi-class)
# Predict pricing tier from: total_orders, avg_quantity, total_revenue
# ══════════════════════════════════════════════════════

features = ["total_orders", "avg_quantity", "total_revenue"]
X = cust_df[features].values
scaler = StandardScaler()
X = scaler.fit_transform(X)

le = LabelEncoder()
y = le.fit_transform(cust_df["pricing_tier"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LogisticRegression(max_iter=5000)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)

print(f"\n📈  Pricing Tier Model Accuracy: {round(acc * 100, 1)}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# ══════════════════════════════════════════════════════
# STEP 3C — HYPOTHESIS TESTING
# H0: Mean revenue is the SAME across all 5 segments
# H1: At least one segment has significantly different mean revenue
# Test: One-way ANOVA
# ══════════════════════════════════════════════════════

segment_groups = [
    group["total_revenue"].values
    for _, group in cust_df.groupby("segment")
]

f_stat, p_value = stats.f_oneway(*segment_groups)

print(f"\n🧪  ANOVA Hypothesis Test")
print(f"    F-statistic : {round(f_stat, 4)}")
print(f"    p-value     : {round(p_value, 6)}")

if p_value < 0.05:
    print("    ✅  Reject H0 — revenue differs significantly across segments (p < 0.05)")
else:
    print("    ❌  Fail to reject H0 — no significant difference found")

# ── Save enriched customer table ─────────────────────────
cust_df.to_csv("customer_segments_enriched.csv", index=False)
print("\n✅  Saved customer_segments_enriched.csv")