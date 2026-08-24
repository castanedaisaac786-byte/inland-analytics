"""
Locate every stale ROAS / spend figure in the repo.
====================================================
The README now reports 3.20x ad-attributed ROAS on $785.00 lifetime spend.
analysis.py, metrics.json, and dashboard.html were never updated, so the
dashboard still renders 5.23x on $673.49. Run this to find every occurrence
before editing anything.

Run from the repo root:  python3 find_stale_roas.py
"""

import json
import pathlib
import re

STALE = ["5.23", "673.49", "3525", "3,525", "35.45"]
SKIP_DIRS = {".git", ".venv", "__pycache__", ".ipynb_checkpoints", "figures"}
SKIP_EXT = {".png", ".jpg", ".xlsx", ".docx", ".bak", ".pdf"}


def scan():
    root = pathlib.Path(".")
    hits = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(d in p.parts for d in SKIP_DIRS) or p.suffix.lower() in SKIP_EXT:
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for token in STALE:
                if token in line:
                    hits += 1
                    print(f"{str(p):<42} :{i:<5} {line.strip()[:96]}")
                    break
    print(f"\n{hits} occurrence(s) of a stale figure.")
    return hits


def check_ad_spend():
    print("\n" + "=" * 74)
    print("data/ad_spend.csv")
    print("=" * 74)
    try:
        import pandas as pd
        ads = pd.read_csv("data/ad_spend.csv")
    except Exception as e:
        print(f"  could not read: {e}")
        return
    col = next((c for c in ads.columns if "spent" in c.lower() or "amount" in c.lower()), None)
    if col is None:
        print(f"  no spend column found. Columns: {list(ads.columns)}")
        return
    total = ads[col].sum()
    print(f"  {len(ads)} rows, column '{col}', total ${total:,.2f}")
    print(f"  README / Part 6 use $785.00 -> difference ${785.00 - total:,.2f}")
    if abs(total - 785.00) > 0.01:
        print("  >> STALE. Add the missing campaign rows so this file is the")
        print("     single source of truth for spend. Do not hardcode 785.00.")
    print()
    print(ads.to_string(index=False))


def check_metrics():
    print("\n" + "=" * 74)
    print("metrics.json headline")
    print("=" * 74)
    try:
        m = json.load(open("metrics.json"))
    except Exception as e:
        print(f"  could not read: {e}")
        return
    for k, v in m.get("headline", {}).items():
        flag = ""
        if k == "meta_roas" and v and abs(float(v) - 5.23) < 0.01:
            flag = "   <- STALE, gross not ad-attributed"
        if k == "total_ad_spend" and v and abs(float(v) - 673.49) < 0.01:
            flag = "   <- STALE, should be 785.00"
        print(f"  {k:<28} {v}{flag}")
    if "meta_roas_attributed" not in m.get("headline", {}):
        print("\n  >> metrics.json has no `meta_roas_attributed` key.")
        print("     Apply patch_analysis.py, then rerun analysis.py.")


if __name__ == "__main__":
    print("=" * 74)
    print("STALE FIGURE SCAN")
    print("=" * 74)
    scan()
    check_ad_spend()
    check_metrics()
    print("\n" + "=" * 74)
    print("ORDER OF OPERATIONS")
    print("=" * 74)
    print("  1. Add the missing campaign rows to data/ad_spend.csv until it")
    print("     totals $785.00. That file should be the only place spend lives.")
    print("  2. python3 patch_analysis.py     (adds the ad_attributed split)")
    print("  3. python3 analysis.py           (regenerates metrics.json)")
    print("  4. Edit dashboard.html by hand — see the scan output above for")
    print("     every hardcoded figure. Label the tile 'Ad-attributed ROAS'.")
    print("  5. Rerun this script. It should find zero occurrences.")
