"""
Patch analysis.py to compute ad-attributed ROAS.
=================================================
Part 6 established that 5 jobs tagged channel="Meta Ads" were organic
Instagram DMs with no ad involved ($1,010 of $3,525). analysis.py still
divides ALL Meta-tagged revenue by total spend, which is what produces the
5.23x on the dashboard.

This adds an `ad_attributed` split. It keeps the gross figure so the
correction is visible rather than silently overwritten, and adds the
correct one alongside it.

Idempotent. Writes analysis.py.bak first.

Run from the repo root:  python3 patch_analysis.py
"""

import pathlib
import shutil

OLD = '''meta_roas = round(meta_revenue / total_ad_spend, 2) if total_ad_spend else None
blended_cost_per_job = round(total_ad_spend / meta_jobs, 2) if meta_jobs else None'''

NEW = '''meta_roas = round(meta_revenue / total_ad_spend, 2) if total_ad_spend else None
blended_cost_per_job = round(total_ad_spend / meta_jobs, 2) if meta_jobs else None

# --- Ad-attributed split (added after the Part 6 audit) -------------------
# Five jobs tagged channel="Meta Ads" were logged as organic Instagram DMs
# or feed visits with no ad involved. Dividing ALL Meta-tagged revenue by
# ad spend overstates ROAS. `ad_attributed` marks the jobs that actually
# came from a paid placement.
if "ad_attributed" in jobs_priced.columns:
    _attr = jobs_priced[
        (jobs_priced["channel"] == "Meta Ads")
        & (jobs_priced["ad_attributed"].fillna(0).astype(int) == 1)
    ]
    _organic = jobs_priced[
        (jobs_priced["channel"] == "Meta Ads")
        & (jobs_priced["ad_attributed"].fillna(0).astype(int) == 0)
    ]
    meta_revenue_attributed = float(_attr["total_clean"].sum())
    meta_jobs_attributed = int(len(_attr))
    meta_revenue_organic = float(_organic["total_clean"].sum())
    meta_jobs_organic = int(len(_organic))
    meta_roas_attributed = (
        round(meta_revenue_attributed / total_ad_spend, 2) if total_ad_spend else None
    )
    cost_per_attributed_job = (
        round(total_ad_spend / meta_jobs_attributed, 2) if meta_jobs_attributed else None
    )
else:
    meta_revenue_attributed = meta_jobs_attributed = None
    meta_revenue_organic = meta_jobs_organic = None
    meta_roas_attributed = cost_per_attributed_job = None
    print("WARNING: job_log.csv has no `ad_attributed` column. "
          "Run migrate_job_log.py — ROAS below is GROSS and overstated.")
# -------------------------------------------------------------------------'''

OLD_HEADLINE = '''        "meta_roas": meta_roas,
        "blended_cost_per_meta_job": blended_cost_per_job,'''

NEW_HEADLINE = '''        "meta_roas": meta_roas,
        "meta_roas_label": "GROSS - includes organic inquiries mistagged as Meta Ads",
        "blended_cost_per_meta_job": blended_cost_per_job,
        "meta_revenue_attributed": meta_revenue_attributed,
        "meta_jobs_attributed": meta_jobs_attributed,
        "meta_revenue_organic": meta_revenue_organic,
        "meta_jobs_organic": meta_jobs_organic,
        "meta_roas_attributed": meta_roas_attributed,
        "meta_roas_attributed_label": "CORRECT - paid placements only. Use this one.",
        "cost_per_attributed_job": cost_per_attributed_job,'''

NOTE_ANCHOR = '''        f"trusting the sheet's own total."
    ),'''

NOTE_NEW = '''        f"trusting the sheet's own total. "
        f"ATTRIBUTION: {meta_jobs_organic} job(s) worth "
        f"${meta_revenue_organic:,.0f} were tagged channel='Meta Ads' but logged "
        f"as organic Instagram inquiries with no ad involved. Headline ROAS of "
        f"{meta_roas}x is GROSS and overstated; ad-attributed ROAS is "
        f"{meta_roas_attributed}x. Revenue is also gross of labour — nearly every "
        f"job is worked on a revenue split, so the real break-even is 2x ROAS."
        if meta_jobs_organic is not None else
        f"trusting the sheet's own total."
    ),'''


def main():
    p = pathlib.Path("analysis.py")
    if not p.exists():
        raise SystemExit("analysis.py not found — run from the repo root.")

    t = p.read_text()
    if "meta_roas_attributed" in t:
        print("Already patched. Nothing to do.")
        return

    shutil.copy(p, "analysis.py.bak")
    applied = []

    for name, old, new in [("ROAS split", OLD, NEW),
                           ("headline keys", OLD_HEADLINE, NEW_HEADLINE),
                           ("data quality note", NOTE_ANCHOR, NOTE_NEW)]:
        if old in t:
            t = t.replace(old, new, 1)
            applied.append(name)
        else:
            print(f"  SKIP: could not find the anchor for '{name}' — patch by hand.")

    p.write_text(t)
    print(f"Backed up to analysis.py.bak")
    print(f"Applied: {', '.join(applied) if applied else 'nothing'}")
    print("\nNext:  python3 analysis.py")
    print("Then check metrics.json for `meta_roas_attributed`.")


if __name__ == "__main__":
    main()
