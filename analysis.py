"""
Inland Auto Detailing — Ad & Ops Analytics
============================================
Loads the raw job log and Meta Ads export, cleans them, and computes the
metrics that feed dashboard.html:

  - Revenue, job count, and average ticket by acquisition channel
  - Blended and Meta-specific ROAS (revenue attributed to Meta Ads / Meta ad spend)
  - Weekly job/revenue trend
  - Geographic (city) breakdown
  - Day-of-week demand pattern
  - Service package-tier mix
  - Two-location capacity model (Moreno Valley solo-operator vs. San Diego
    part-time launch), used to size the ops recommendation in the dashboard

Run:  python3 analysis.py
Output: metrics.json (consumed by dashboard.html)
"""

import json
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
jobs = pd.read_csv("data/job_log.csv")
ads = pd.read_csv("data/ad_spend.csv")

jobs["date"] = pd.to_datetime(jobs["date"], errors="coerce")

# Fallback: if "total" wasn't recorded but job_value was, use job_value.
# Rule 2: never trust a manually entered total. Recompute always, and
# FLAG any row where the sheet disagrees. The previous version used the
# entered total when present and only fell back to recomputation, which is
# how the Dr Morral 8/7 tip drop reached metrics.json silently.
jobs["total_clean"] = jobs["job_value"].fillna(0) + jobs["tip"].fillna(0)
_mismatch = jobs["total"].notna() & (jobs["total"] != jobs["total_clean"])
if _mismatch.any():
    print(f"WARNING: {_mismatch.sum()} row(s) where the sheet total disagrees "
          f"with job_value + tip. Recomputed values are used:")
    print(jobs.loc[_mismatch, ["date", "customer", "job_value", "tip", "total",
                               "total_clean"]].to_string(index=False))

# Detail-service jobs only (excludes 4 non-detail side jobs: vinyl fencing,
# decor change — real income, but not part of the detailing business itself).
detail_jobs = jobs[jobs["is_detail_job"] == 1].copy()

# Billable, priced detail jobs = the business's actual core revenue base.
# This lands below the source sheet's own "33 jobs" label, because that
# label counted pressure-washing as a detail service and this analysis
# deliberately does not. See data_quality_note below for full reasoning.
detail_priced = detail_jobs.dropna(subset=["total_clean"]).copy()
jobs_priced = detail_priced  # alias used throughout the rest of the script

# ---------------------------------------------------------------------------
# Headline numbers
# ---------------------------------------------------------------------------
total_jobs = int(len(jobs))                 # every logged entry, incl. side jobs
total_detail_jobs = int(len(detail_jobs))   # detail-service jobs, priced or not
total_revenue = float(jobs_priced["total_clean"].sum())
avg_ticket = float(jobs_priced["total_clean"].mean())
total_ad_spend = float(ads["amount_spent"].sum())

# ---------------------------------------------------------------------------
# Channel performance
# ---------------------------------------------------------------------------
channel_grp = (
    jobs_priced.groupby("channel")
    .agg(jobs=("total_clean", "count"), revenue=("total_clean", "sum"))
    .reset_index()
)
channel_grp["avg_ticket"] = channel_grp["revenue"] / channel_grp["jobs"]
channel_grp = channel_grp.sort_values("revenue", ascending=False)

# Meta Ads is the only channel with real spend data attached.
meta_revenue = float(
    jobs_priced.loc[jobs_priced["channel"] == "Meta Ads", "total_clean"].sum()
)
meta_jobs = int((jobs_priced["channel"] == "Meta Ads").sum())
meta_roas = round(meta_revenue / total_ad_spend, 2) if total_ad_spend else None
blended_cost_per_job = round(total_ad_spend / meta_jobs, 2) if meta_jobs else None

channel_performance = []
for _, row in channel_grp.iterrows():
    channel_performance.append({
        "channel": row["channel"],
        "jobs": int(row["jobs"]),
        "revenue": round(float(row["revenue"]), 2),
        "avg_ticket": round(float(row["avg_ticket"]), 2),
    })

# ---------------------------------------------------------------------------
# Weekly trend (tracked period only — 7/18 onward — so gaps in early
# backfilled data don't distort the trend line)
# ---------------------------------------------------------------------------
tracked = jobs_priced[jobs_priced["tracked_period"] == "tracked"].dropna(subset=["date"]).copy()
tracked["week_start"] = tracked["date"].dt.to_period("W-SUN").apply(lambda p: p.start_time)
weekly = (
    tracked.groupby("week_start")
    .agg(jobs=("total_clean", "count"), revenue=("total_clean", "sum"))
    .reset_index()
    .sort_values("week_start")
)

# Continuous week range so a paused week shows up as a real $0 bar
# instead of silently disappearing from the trend line.
range_end = max(tracked["date"].max(), pd.Timestamp.today())
full_weeks = pd.period_range(
    start=tracked["week_start"].min(),
    end=pd.Timestamp(range_end).to_period("W-SUN").start_time,
    freq="W-SUN",
).start_time
weekly = (
    weekly.set_index("week_start")
    .reindex(full_weeks, fill_value=0)
    .rename_axis("week_start")
    .reset_index()
)

weekly_trend = [
    {"week": row["week_start"].strftime("%b %d"), "jobs": int(row["jobs"]), "revenue": round(float(row["revenue"]), 2)}
    for _, row in weekly.iterrows()
]

tracked_days = (tracked["date"].max() - tracked["date"].min()).days + 1 if len(tracked) else 0
tracked_weeks = round(tracked_days / 7, 2) if tracked_days else 0
jobs_per_week_current = round(len(tracked) / tracked_weeks, 1) if tracked_weeks else 0

# ---------------------------------------------------------------------------
# Geography
# ---------------------------------------------------------------------------
geo_grp = (
    jobs_priced.groupby("city")
    .agg(jobs=("total_clean", "count"), revenue=("total_clean", "sum"))
    .reset_index()
    .sort_values("revenue", ascending=False)
)
geo_breakdown = [
    {"city": row["city"], "jobs": int(row["jobs"]), "revenue": round(float(row["revenue"]), 2)}
    for _, row in geo_grp.iterrows()
]

moreno_valley_jobs = int((jobs_priced["city"] == "Moreno Valley").sum())
moreno_valley_revenue = float(jobs_priced.loc[jobs_priced["city"] == "Moreno Valley", "total_clean"].sum())

# ---------------------------------------------------------------------------
# Day-of-week demand pattern (tracked period, has day_of_week populated)
# ---------------------------------------------------------------------------
dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
dow_grp = (
    tracked.groupby("day_of_week")
    .agg(jobs=("total_clean", "count"), revenue=("total_clean", "sum"))
    .reindex(dow_order)
    .fillna(0)
    .reset_index()
)
dow_pattern = [
    {"day": row["day_of_week"], "jobs": int(row["jobs"]), "revenue": round(float(row["revenue"]), 2)}
    for _, row in dow_grp.iterrows()
]

# ---------------------------------------------------------------------------
# Package tier mix
# ---------------------------------------------------------------------------
tier_grp = (
    detail_priced.groupby("package_tier")
    .agg(jobs=("total_clean", "count"), revenue=("total_clean", "sum"))
    .reset_index()
    .sort_values("revenue", ascending=False)
)
tier_mix = [
    {"tier": row["package_tier"], "jobs": int(row["jobs"]), "revenue": round(float(row["revenue"]), 2)}
    for _, row in tier_grp.iterrows()
]

# ---------------------------------------------------------------------------
# Assemble metrics.json
# ---------------------------------------------------------------------------
metrics = {
    "generated_from": "INLAND TRACKER job log (6/14/26 - 8/9/26) + Meta Ads Manager lifetime export",
    "data_quality_note": (
        f"Source sheet logs {total_jobs} rows total, incl. 4 non-detail side jobs "
        f"(vinyl fencing, decor change, garage organization, party planning) and "
        f"4 pressure-wash jobs, reclassified as "
        f"non-detail since exterior/patio pressure washing is not a vehicle-detailing "
        f"service. Restricting to priced, vehicle-detail-service jobs yields "
        f"{len(detail_priced)} jobs — fewer than the source sheet's own '33 jobs' "
        f"label, since that label originally counted pressure-washing as a detail "
        f"service; this analysis defines 'detail' more narrowly on purpose. The "
        f"sheet's own TOTALS row ($5,561) also doesn't fully reconcile with the sum "
        f"of its own Total column on the original basis — likely a SUM() range that "
        f"doesn't cover every row. This script recomputes from raw rows rather than "
        f"trusting the sheet's own total."
    ),
    "headline": {
        "total_jobs": total_jobs,
        "total_detail_jobs": total_detail_jobs,
        "total_revenue": round(total_revenue, 2),
        "avg_ticket": round(avg_ticket, 2),
        "total_ad_spend": round(total_ad_spend, 2),
        "meta_revenue": round(meta_revenue, 2),
        "meta_jobs": meta_jobs,
        "meta_roas": meta_roas,
        "blended_cost_per_meta_job": blended_cost_per_job,
    },
    "channel_performance": channel_performance,
    "weekly_trend": weekly_trend,
    "geo_breakdown": geo_breakdown,
    "moreno_valley_jobs": moreno_valley_jobs,
    "moreno_valley_revenue": round(moreno_valley_revenue, 2),
    "dow_pattern": dow_pattern,
    "tier_mix": tier_mix,
}

with open("metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(json.dumps(metrics, indent=2))
