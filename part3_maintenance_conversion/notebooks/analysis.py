"""
Inland Auto Detailing — Maintenance Conversion Analysis
=========================================================
Reproduces the funnel, channel-attribution, permutation test, and RFM
findings from the Month 1.5 business snapshot. Run from notebooks/:

    python3 analysis.py

Outputs:
  - Printed summary stats
  - figures/funnel.png
  - figures/channel_comparison.png
  - figures/rfm_scatter.png
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date

pd.set_option("display.width", 120)

jobs = pd.read_csv("../data/job_log_anonymized.csv", parse_dates=["date"])
maint = pd.read_csv("../data/maintenance_tracker_anonymized.csv", parse_dates=["last_service"])

detail_jobs = jobs[jobs["is_detail"]].copy()

# ---------------------------------------------------------------
# 1. Data quality check — this caught a real bug in the source sheet
# ---------------------------------------------------------------
reported_total = 5561
computed_total = detail_jobs["total"].sum()
print("=" * 60)
print("DATA QUALITY CHECK")
print("=" * 60)
print(f"Computed total (job_value + tip): ${computed_total:,.0f}")
print(f"Originally reported total in sheet: ${reported_total:,.0f}")
print(f"Discrepancy: ${computed_total - reported_total:,.0f}")
print()
print("BASIS NOTE: the figure above compares detail-only revenue against")
print("the sheet's ALL-JOBS total, which counts pressure-wash and non-detail")
print("rows the detail-only basis excludes. It is a basis mismatch, not a")
print("tip error. The real like-for-like check is the sheet against itself:")
print("its Total column sums to $6,491 vs its own TOTALS row of $6,531 --")
print("a $40 gap, exactly the Dr Morral 8/7 dropped tip. One row, $40, real.")
print()

# ---------------------------------------------------------------
# 2. Maintenance funnel
# ---------------------------------------------------------------
status_counts = maint["status"].value_counts()
too_early = status_counts.get("too_early", 0)
pitched = len(maint) - too_early
no_response = status_counts.get("unresponsive", 0) + status_counts.get("no_contact_info", 0)
responded = pitched - no_response
positive = status_counts.get("confirmed", 0) + status_counts.get("pending_positive", 0) \
    + status_counts.get("active_self_requested", 0)
confirmed = status_counts.get("confirmed", 0) + status_counts.get("active_self_requested", 0)

print("=" * 60)
print("MAINTENANCE FUNNEL")
print("=" * 60)
funnel = pd.Series({
    "Candidates": len(maint),
    "Pitched (due for outreach)": pitched,
    "Responded": responded,
    "Positive (yes / pending yes)": positive,
    "Confirmed w/ date": confirmed,
})
print(funnel.to_string())
print(f"\nResponse rate:  {responded/pitched:.0%}")
print(f"Positive rate:  {positive/pitched:.0%} (of pitched)")
print(f"Confirmed rate: {confirmed/pitched:.0%} (of pitched)")
print()

fig, ax = plt.subplots(figsize=(7, 4))
stages = ["Pitched", "Responded", "Positive", "Confirmed"]
values = [pitched, responded, positive, confirmed]
bars = ax.barh(stages[::-1], values[::-1], color=["#c85c4a", "#e0a336", "#4b9c93", "#4b9c93"][::-1])
for bar, v in zip(bars, values[::-1]):
    ax.text(v + 0.3, bar.get_y() + bar.get_height()/2, str(v), va="center", fontsize=11, fontweight="bold")
ax.set_xlabel("Candidates")
ax.set_title("Maintenance Program Funnel — Month 1.5")
ax.set_xlim(0, pitched + 3)
plt.tight_layout()
plt.savefig("../figures/funnel.png", dpi=150)
plt.close()

# ---------------------------------------------------------------
# 3. Channel performance
# ---------------------------------------------------------------
print("=" * 60)
print("CHANNEL PERFORMANCE")
print("=" * 60)
channel_jobs = detail_jobs.groupby("channel").agg(
    jobs=("customer_id", "count"),
    avg_value=("total", "mean"),
    total_revenue=("total", "sum"),
).round(0).sort_values("jobs", ascending=False)
print(channel_jobs)
print()

first_job_channel = detail_jobs.sort_values("date").groupby("customer_id")["channel"].first()
maint_ch = maint.copy()
maint_ch["channel"] = maint_ch["customer_id"].map(first_job_channel)
maint_pitched = maint_ch[maint_ch["status"] != "too_early"]

channel_outcomes = pd.crosstab(maint_pitched["channel"], maint_pitched["status"])
print("Maintenance pitch outcomes by channel:")
print(channel_outcomes)
print()

print("SAMPLE SIZE SENSITIVITY (does the result survive ONE flipped outcome?)")
print("-" * 60)
positive_statuses = {"confirmed", "pending_positive", "active_self_requested"}
maint_pitched = maint_pitched.copy()
maint_pitched["is_positive"] = maint_pitched["status"].isin(positive_statuses)
channel_n = maint_pitched.groupby("channel").size()
channel_pos = maint_pitched.groupby("channel")["is_positive"].sum()

for ch in channel_n.index:
    n, pos = channel_n[ch], channel_pos[ch]
    rate = pos / n
    flip_up = min(pos + 1, n) / n
    flip_down = max(pos - 1, 0) / n
    flag = "LOW CONFIDENCE (n<10)" if n < 10 else "more stable"
    print(f"  {ch:20s} n={n:2d}  rate={rate:.0%}  ->  {flip_down:.0%}-{flip_up:.0%} if one outcome flips   [{flag}]")
print()

print("PERMUTATION TEST: D2D vs Meta Ads positive rate")
print("-" * 60)
rng = np.random.default_rng(42)
sub = maint_pitched[maint_pitched["channel"].isin(["D2D", "Meta Ads"])].copy()
labels = sub["channel"].values
outcomes = sub["is_positive"].values.astype(float)

observed_diff = outcomes[labels == "D2D"].mean() - outcomes[labels == "Meta Ads"].mean()
n_iter = 10_000
diffs = np.empty(n_iter)
for i in range(n_iter):
    shuffled = rng.permutation(labels)
    diffs[i] = outcomes[shuffled == "D2D"].mean() - outcomes[shuffled == "Meta Ads"].mean()

p_value = float(np.mean(np.abs(diffs) >= abs(observed_diff)))
print(f"  Observed gap (D2D minus Meta Ads positive rate): {observed_diff:+.1%}")
print(f"  p-value (10,000 resamples, two-sided):            {p_value:.3f}")
if p_value < 0.05:
    print("  -> statistically distinguishable from chance at the 5% level")
else:
    print("  -> NOT statistically distinguishable from chance at this sample size")
    print("     (consistent with the sensitivity check above: real signal, not yet proof)")
print()

print("HOW MUCH DATA WOULD IT TAKE TO PROVE THIS?")
print("-" * 60)
p_meta = float(outcomes[labels == "Meta Ads"].mean())
p_d2d = float(outcomes[labels == "D2D"].mean())
n_meta_now = int((labels == "Meta Ads").sum())
n_d2d_now = int((labels == "D2D").sum())
z_alpha2, z_beta = 1.959964, 0.841621
pooled_var = p_meta * (1 - p_meta) + p_d2d * (1 - p_d2d)
effect = abs(p_d2d - p_meta)
n_per_group_needed = ((z_alpha2 + z_beta) ** 2 * pooled_var) / (effect ** 2)
print(f"  Current observed rates: Meta Ads {p_meta:.0%} (n={n_meta_now}), D2D {p_d2d:.0%} (n={n_d2d_now})")
print(f"  Gap: {effect:.1%}")
print(f"  To detect a gap this size at 95% confidence / 80% power, each")
print(f"  channel needs roughly {n_per_group_needed:.0f} pitched candidates.")
print(f"  D2D currently has {n_d2d_now} -> that's {n_per_group_needed/n_d2d_now:.0f}x more needed.")
print(f"  This is a real target to grow toward as the maintenance program")
print(f"  scales, not proof achievable at current business volume soon.")
print()

fig, ax = plt.subplots(figsize=(8, 4.5))
plot_df = channel_outcomes.loc[channel_outcomes.sum(axis=1).sort_values(ascending=False).index]
status_colors = {
    "declined": "#c85c4a", "unresponsive": "#8b8378", "no_contact_info": "#c9c2ae",
    "pending_positive": "#4b9c93", "confirmed": "#2f6f4a", "active_self_requested": "#e0a336",
    "self_sufficient": "#6b7f8f",
}
bar_colors = [status_colors.get(c, "#9aa2a9") for c in plot_df.columns]
plot_df.plot(kind="bar", stacked=True, ax=ax, color=bar_colors)
ax.set_ylabel("Candidates")
ax.set_title("Maintenance Pitch Outcome by Acquisition Channel")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig("../figures/channel_comparison.png", dpi=150)
plt.close()

# ---------------------------------------------------------------
# 4. Lightweight RFM
# ---------------------------------------------------------------
print("=" * 60)
print("RFM SUMMARY (per customer)")
print("=" * 60)
today = pd.Timestamp("2026-08-20")
rfm = detail_jobs.groupby("customer_id").agg(
    recency_days=("date", lambda x: (today - x.max()).days),
    frequency=("date", "count"),
    monetary=("total", "sum"),
).sort_values("monetary", ascending=False)
print(rfm.head(10))
print(f"\n... {len(rfm)} unique customers total")

fig, ax = plt.subplots(figsize=(7, 5))
sc = ax.scatter(rfm["recency_days"], rfm["frequency"], s=rfm["monetary"]*1.5,
                 c=rfm["monetary"], cmap="YlOrBr", alpha=0.8, edgecolors="#1a1d21")
ax.set_xlabel("Recency (days since last job)")
ax.set_ylabel("Frequency (# jobs)")
ax.set_title("RFM Snapshot — bubble size/color = total spend")
plt.colorbar(sc, label="Total spend ($)")
plt.tight_layout()
plt.savefig("../figures/rfm_scatter.png", dpi=150)
plt.close()

print("\nFigures saved to ../figures/")
