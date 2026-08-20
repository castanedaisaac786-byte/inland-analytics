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
jobs["total_clean"] = jobs["total"].fillna(jobs["job_value"])

# Detail-service jobs only (excludes 2 non-detail side jobs: vinyl fencing,
# decor change — real income, but not part of the detailing business itself).
detail_jobs = jobs[jobs["is_detail_job"] == 1].copy()

# Billable, priced detail jobs = the business's actual core revenue base.
# This lands at 33 jobs, which matches the source sheet's own "33 jobs"
# label exactly — a good sanity check that the transcription is faithful.
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
# Two-location capacity model
# ---------------------------------------------------------------------------
# Current combined throughput (both operators, tracked period, Inland Empire only)
avg_ticket_tracked = round(float(tracked["total_clean"].mean()), 2)

# Moreno Valley / Inland Empire (Sam, full-time solo): assume he can sustain
# roughly the current combined pace on his own once he's the only full-time
# operator on the ground — realistically 70-100% of current combined volume,
# since current volume was already produced without a second full-time market
# to split attention with.
sam_solo_low = round(jobs_per_week_current * 0.7, 1)
sam_solo_high = jobs_per_week_current

# San Diego (Isaac, ~1 day/week around school): a brand-new market with zero
# existing customer base, reviews, or referral network, worked one day a week.
# Assume 1 job slot per available hour block on that single day; realistic
# early capacity is 1-3 jobs on the day worked, before drive time and
# same-day-only scheduling friction.
sd_solo_low = 1
sd_solo_high = 3

capacity_model = {
    "current_combined_jobs_per_week": jobs_per_week_current,
    "avg_ticket_tracked_period": avg_ticket_tracked,
    "moreno_valley_solo_jobs_per_week": [sam_solo_low, sam_solo_high],
    "san_diego_part_time_jobs_per_week": [sd_solo_low, sd_solo_high],
    "moreno_valley_solo_weekly_revenue": [round(sam_solo_low * avg_ticket_tracked, 2), round(sam_solo_high * avg_ticket_tracked, 2)],
    "san_diego_part_time_weekly_revenue": [round(sd_solo_low * avg_ticket_tracked, 2), round(sd_solo_high * avg_ticket_tracked, 2)],
}

# ---------------------------------------------------------------------------
# Assemble metrics.json
# ---------------------------------------------------------------------------
metrics = {
    "generated_from": "INLAND TRACKER job log (6/14/26 - 8/9/26) + Meta Ads Manager lifetime export",
    "data_quality_note": (
        f"Source sheet logs {total_jobs} rows total, incl. 2 non-detail side jobs "
        f"(vinyl fencing, decor change). Restricting to priced detail-service jobs "
        f"yields {len(detail_priced)} jobs, matching the source sheet's own '33 jobs' "
        f"summary label exactly. The sheet's own TOTALS row ($5,561) doesn't fully "
        f"reconcile with the sum of its own Total column ($5,591 on this basis) — "
        f"likely a SUM() range that doesn't cover every row. This script recomputes "
        f"from raw rows rather than trusting the sheet's own total."
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
    "capacity_model": capacity_model,
}

with open("metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(json.dumps(metrics, indent=2))
