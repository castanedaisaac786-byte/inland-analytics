"""
One-command refresh for the whole repo.
Run this after updating data/job_log.csv, data/ad_spend.csv, or
part3_maintenance_conversion/data/*.csv with new jobs/campaigns/pitches.

    python3 refresh.py

What it does:
  1. Reruns analysis.py -> regenerates metrics.json from the raw CSVs
  2. Resyncs dashboard.html's embedded METRICS block with the new metrics.json
  3. Reruns Part 3's analysis.py -> regenerates the funnel/channel/
     permutation-test/power-calculation numbers
  4. Prints a before/after summary of the headline numbers so you can
     eyeball whether anything moved further than you'd expect

What it does NOT do (still manual, on purpose):
  - Entering new rows into the CSVs in the first place
  - Updating written prose claims in README.md (e.g. "$186 vs $129") --
    those are English sentences, not generated output, so they only
    stay honest if you re-read them against this script's printed
    numbers each time and edit by hand when they've drifted
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    return result.stdout


def load_headline():
    try:
        with open(ROOT / "metrics.json") as f:
            return json.load(f)["headline"]
    except FileNotFoundError:
        return None


print("=" * 60)
print("STEP 1: Rerunning Part 1 analysis (analysis.py)")
print("=" * 60)
before = load_headline()
run(["python3", "analysis.py"], cwd=ROOT)
after = load_headline()

if before:
    print("Headline changes:")
    for key in after:
        b, a = before.get(key), after.get(key)
        flag = "  <-- CHANGED" if b != a else ""
        print(f"  {key:24s} {b} -> {a}{flag}")
else:
    print("No prior metrics.json found (first run) -- current values:")
    for key, val in after.items():
        print(f"  {key:24s} {val}")
print()

print("=" * 60)
print("STEP 2: Resyncing dashboard.html")
print("=" * 60)
with open(ROOT / "metrics.json") as f:
    new_metrics = f.read()
with open(ROOT / "dashboard.html") as f:
    html = f.read()
start = html.find("const METRICS = {")
end = html.find("\nconst money = n =>")
if start == -1 or end == -1:
    print("WARNING: could not find METRICS block anchors in dashboard.html.")
    print("dashboard.html was NOT modified -- resync it manually this time")
    print("and paste the anchor lines back to Claude so refresh.py can be fixed.")
else:
    html = html[:start] + "const METRICS = " + new_metrics.strip() + ";" + html[end:]
    with open(ROOT / "dashboard.html", "w") as f:
        f.write(html)
    print("dashboard.html updated.")
print()

print("=" * 60)
print("STEP 3: Rerunning Part 3 analysis (maintenance conversion)")
print("=" * 60)
part3_dir = ROOT / "part3_maintenance_conversion" / "notebooks"
if part3_dir.exists():
    out = run(["python3", "analysis.py"], cwd=part3_dir)
    # Surface just the headline numbers a reader would care about
    for line in out.splitlines():
        if any(k in line for k in ["Response rate", "Positive rate", "Confirmed rate",
                                     "Observed gap", "p-value", "channel needs roughly"]):
            print(" ", line.strip())
else:
    print("part3_maintenance_conversion/notebooks not found -- skipped.")
print()

print("=" * 60)
print("DONE. Next steps:")
print("=" * 60)
print("  1. Open dashboard.html and eyeball it")
print("  2. Compare README.md's written claims against the numbers above --")
print("     update any sentence that quotes a specific $ or % that moved")
print("  3. git add . && git commit -m '...' && git push")
