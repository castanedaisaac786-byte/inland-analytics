"""
Adds today's two new jobs (Dr Morral garage-organize backfill, Lucero
party planning) to job_log.csv and job_log_with_gender.csv, and updates
the data_quality_note text to mention the new non-detail job types.

Run once from the repo root:
    python3 add_new_jobs.py
"""
import pandas as pd

# ---------------------------------------------------------------
# 1. job_log.csv
# ---------------------------------------------------------------
df = pd.read_csv("data/job_log.csv")

pre_718_period = df.loc[df["customer"] == "Al", "tracked_period"].iloc[0]
tracked_period = df.loc[df["customer"] == "Emmanuel", "tracked_period"].iloc[0]

new_rows = pd.DataFrame([
    {
        "date": "07/03/2026", "day_of_week": None, "time_of_day": None,
        "customer": "Dr Morral", "city": "Riverside", "service": "Garage Organize",
        "package_tier": "Other (non-detail)", "vehicles": 1, "channel": "D2D",
        "job_value": 160, "tip": 0, "total": 160,
        "tracked_period": pre_718_period, "is_detail_job": 0,
        "notes": "Backfilled; posted about this job, which led to the Lucero booking",
    },
    {
        "date": "08/22/2026", "day_of_week": "Fri", "time_of_day": "4:30-9 PM",
        "customer": "Lucero", "city": "Perris", "service": "Party Planning / Loading Unload",
        "package_tier": "Other (non-detail)", "vehicles": 1, "channel": "D2D",
        "job_value": 170, "tip": 20, "total": 190,
        "tracked_period": tracked_period, "is_detail_job": 0,
        "notes": "Knocked on her door a month ago; saw the garage-organize post",
    },
])

before = len(df)
df = pd.concat([df, new_rows], ignore_index=True)
df.to_csv("data/job_log.csv", index=False)
print(f"job_log.csv: {before} -> {len(df)} rows")

# ---------------------------------------------------------------
# 2. job_log_with_gender.csv (different, simpler schema)
# ---------------------------------------------------------------
dfg = pd.read_csv("data/job_log_with_gender.csv")
new_rows_g = pd.DataFrame([
    {
        "date": "07/03/2026", "customer": "Dr Morral", "city": "Riverside",
        "service": "Garage Organize", "package_tier": "Other (non-detail)",
        "vehicles": 1, "acquisition_channel": "D2D", "job_value": 160,
        "tip": 0, "total": 160,
        "notes": "Backfilled; led to Lucero booking", "gender": "Male",
    },
    {
        "date": "08/22/2026", "customer": "Lucero", "city": "Perris",
        "service": "Party Planning / Loading Unload", "package_tier": "Other (non-detail)",
        "vehicles": 1, "acquisition_channel": "D2D", "job_value": 170,
        "tip": 20, "total": 190,
        "notes": "Knocked on her door a month ago", "gender": "Female",
    },
])
before_g = len(dfg)
dfg = pd.concat([dfg, new_rows_g], ignore_index=True)
dfg.to_csv("data/job_log_with_gender.csv", index=False)
print(f"job_log_with_gender.csv: {before_g} -> {len(dfg)} rows")

# ---------------------------------------------------------------
# 3. Update the data_quality_note text to mention the new job types
# ---------------------------------------------------------------
with open("analysis.py") as f:
    content = f.read()

old = '''f"Source sheet logs {total_jobs} rows total, incl. 2 non-detail side jobs "
        f"(vinyl fencing, decor change) and 4 pressure-wash jobs, reclassified as "'''

new = '''f"Source sheet logs {total_jobs} rows total, incl. 4 non-detail side jobs "
        f"(vinyl fencing, decor change, garage organization, party planning) and "
        f"4 pressure-wash jobs, reclassified as "'''

if old not in content:
    print("NO MATCH FOUND for data_quality_note text -- nothing changed there.")
    print("(The row additions above still succeeded either way.)")
else:
    content = content.replace(old, new)
    with open("analysis.py", "w") as f:
        f.write(content)
    print("analysis.py data_quality_note text updated.")
