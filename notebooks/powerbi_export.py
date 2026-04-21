import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ══════════════════════════════════════════════════════
# STEP 4A — PREPARE POWER BI EXPORT FILES
# (Power BI imports CSVs directly — these are your 3 tables)
# ══════════════════════════════════════════════════════

transactions  = pd.read_csv("../data/raw_transactions.csv", parse_dates=["date"])
cust_segments = pd.read_csv("../data/customer_segments_enriched.csv")
products      = pd.read_csv("../data/product_summary.csv")

# Merge segment info onto transactions for the main fact table
fact_table = transactions.merge(
    cust_segments[["customer_id", "segment", "pricing_tier", "cumulative_revenue_pct"]],
    on="customer_id",
    how="left"
)

# Add time dimensions (useful for Power BI time intelligence)
fact_table["year"]    = fact_table["date"].dt.year
fact_table["month"]   = fact_table["date"].dt.month
fact_table["quarter"] = fact_table["date"].dt.quarter

# KPI: retention proxy — customers who transacted in both 2023 & 2024
years_active = transactions.groupby("customer_id")["date"].apply(
    lambda x: x.dt.year.nunique()
)
cust_segments["retained"] = cust_segments["customer_id"].map(years_active).apply(
    lambda x: "Yes" if x > 1 else "No"
)
retention_rate = round(
    cust_segments["retained"].value_counts(normalize=True).get("Yes", 0) * 100, 1
)
print(f"📊  Overall retention rate (2023→2024): {retention_rate}%")

# Save Power BI tables
fact_table.to_csv("../data/PBI_fact_transactions.csv", index=False)
cust_segments.to_csv("../data/PBI_dim_customers.csv", index=False)
products.to_csv("../data/PBI_dim_products.csv", index=False)
plt.savefig("../outputs/pareto_chart.png", dpi=150)
# ══════════════════════════════════════════════════════
# STEP 4B — PARETO CHART (for portfolio / interview)
# ══════════════════════════════════════════════════════

fig, ax1 = plt.subplots(figsize=(12, 6))

# Bar — revenue per customer rank
top_n = 100   # show top 100 for readability
bar_data = cust_segments.head(top_n)

colors = bar_data["segment"].map({
    "Tier 1 – Top":    "#003087",   # Pfizer dark blue
    "Tier 2 – Core":   "#0072CE",
    "Tier 3 – Growth": "#6CACE4",
    "Tier 4 – Tail":   "#BFD7ED",
})

ax1.bar(range(top_n), bar_data["total_revenue"], color=colors, alpha=0.85)
ax1.set_xlabel("Customer Rank (by Revenue)", fontsize=12)
ax1.set_ylabel("Total Revenue ($)", fontsize=12, color="#003087")
ax1.tick_params(axis="y", labelcolor="#003087")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

# Line — cumulative % on second axis
ax2 = ax1.twinx()
ax2.plot(
    range(top_n),
    bar_data["cumulative_revenue_pct"],
    color="#E31837",
    linewidth=2.5,
    label="Cumulative Revenue %"
)
ax2.axhline(78, color="#E31837", linestyle="--", linewidth=1.2, alpha=0.6)
ax2.set_ylabel("Cumulative Revenue %", fontsize=12, color="#E31837")
ax2.tick_params(axis="y", labelcolor="#E31837")
ax2.set_ylim(0, 105)

# Annotations
ax2.annotate(
    "Top 20% → 78% of Revenue",
    xy=(top_n * 0.2, 78),
    xytext=(top_n * 0.35, 65),
    fontsize=10,
    color="#E31837",
    arrowprops=dict(arrowstyle="->", color="#E31837"),
)

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="#003087", label="Tier 1 – Top"),
    Patch(facecolor="#0072CE", label="Tier 2 – Core"),
    Patch(facecolor="#6CACE4", label="Tier 3 – Growth"),
    Patch(facecolor="#BFD7ED", label="Tier 4 – Tail"),
]
ax1.legend(handles=legend_elements, loc="center right", fontsize=9)

plt.title("80/20 Customer Segmentation — Pareto Analysis", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("../outputs/pareto_chart.png", dpi=150, bbox_inches="tight")
plt.show()
print("✅  pareto_chart.png saved")

# ══════════════════════════════════════════════════════
# STEP 4C — KPI SUMMARY PRINTOUT (for your reference)
# ══════════════════════════════════════════════════════

total_rev       = cust_segments["total_revenue"].sum()
top20           = cust_segments.head(int(len(cust_segments) * 0.20))
top20_rev_pct   = round(top20["total_revenue"].sum() / total_rev * 100, 1)
n_segments      = cust_segments["segment"].nunique()

print("\n──────────────────────────────────────")
print("  DASHBOARD KPI SUMMARY")
print("──────────────────────────────────────")
print(f"  Total Customers          : {len(cust_segments):,}")
print(f"  Total Revenue            : ${total_rev:,.0f}")
print(f"  Top 20% Revenue Share    : {top20_rev_pct}%")
print(f"  Number of Segments       : {n_segments}")
print(f"  Customer Retention Rate  : {retention_rate}%")
print("──────────────────────────────────────")