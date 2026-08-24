"""
Close the remaining audit findings.
====================================
Run from the repo root:  python3 fix_audit_items.py

Fixes, with the audit finding each closes:

  a3  Part 5 benchmark mixes two creatives (26 msgs belongs to "Real results",
      2 bookings to Denise). Correct denominator is 49.
  a6  part6 docstring says 3.73x / 40% while its own code prints 3.20x / 63%.
  a6  analysis.py comment says "2 non-detail side jobs"; there are 4.
  a6  ads_analyzer says "16 real past campaigns"; the dataset has 14.
  a7  Part 5 CURRENT_A ($95.01 / 58) reconciles to no export. Meta says
      $56.61 / 34 for Optimized targeting Camp.
  cr  analysis.py trusts a manually entered total when present; Rule 2 says
      always recompute and flag mismatches.

Every edit is idempotent and backs up the file it touches.
"""
import pathlib
import shutil

FIXES = []


def patch(path, old, new, label):
    p = pathlib.Path(path)
    if not p.exists():
        FIXES.append((label, "SKIP — file not found")); return
    t = p.read_text()
    if new in t:
        FIXES.append((label, "already applied")); return
    if old not in t:
        FIXES.append((label, "SKIP — anchor not found, patch by hand")); return
    if not pathlib.Path(str(p) + ".bak").exists():
        shutil.copy(p, str(p) + ".bak")
    p.write_text(t.replace(old, new, 1))
    FIXES.append((label, "FIXED"))


# ---- a3: Part 5 benchmark denominator -----------------------------------
patch("part5_campaign_experiment.py",
      '''    "messages": 26,
    "bookings": 2,          # from the audited job log, not recall''',
      '''    "messages": 49,         # 17 + 32 across the creative's TWO runs.
                            # The earlier 26 belonged to "Real results, real
                            # feedback" — a different creative. Numerator and
                            # denominator had come from different campaigns.
    "bookings": 2,          # from the audited job log, not recall''',
      "a3  Part 5 benchmark 26 -> 49 messages")

# ---- a7: Part 5 live arm figures ----------------------------------------
patch("part5_campaign_experiment.py",
      'CURRENT_A = {"spend": 95.01, "messages": 58, "bookings": 0}',
      '''# Figures below come from the Meta ad-level export, not the app UI.
# The earlier $95.01 / 58 reconciled to no campaign in any export.
CURRENT_A = {"spend": 56.61, "messages": 34, "bookings": 1}   # Optimized targeting Camp''',
      "a7  Part 5 Arm A -> $56.61 / 34 / 1 booking")

patch("part5_campaign_experiment.py",
      'CURRENT_B = {"spend": 20.72, "leads":     3, "bookings": 1}   # tentative',
      'CURRENT_B = {"spend": 20.77, "leads":     3, "bookings": 0}   # tentative booking not confirmed',
      "a7  Part 5 Arm B -> $20.77 / 3 / 0 confirmed")

# ---- a6: part6 docstring contradicts its own output ---------------------
patch("part6_attribution.py",
      "ROAS is 3.73x, not the 5.23x in the README — a 40% overstatement.",
      "ROAS is 3.20x against a published 5.23x — the published figure was 63%\n   too high. Both the numerator (organic jobs) and the denominator (stale\n   spend of $673.49 vs a true $786.08) were wrong.",
      "a6  part6 docstring 3.73x -> 3.20x")

# ---- a6: analysis.py stale comment --------------------------------------
patch("analysis.py",
      "# Detail-service jobs only (excludes 2 non-detail side jobs: vinyl fencing,",
      "# Detail-service jobs only (excludes 4 non-detail side jobs: vinyl fencing,",
      "a6  analysis.py '2 non-detail' -> 4")

# ---- a6: ads_analyzer campaign count ------------------------------------
for old, new in [("16 real past campaigns", "14 real past campaigns"),
                 ("from 16 real", "from 14 real")]:
    patch("ads_analyzer.py", old, new, "a6  ads_analyzer 16 -> 14 campaigns")

# ---- code review: Rule 2 in analysis.py ---------------------------------
patch("analysis.py",
      'jobs["total_clean"] = jobs["total"].fillna(jobs["job_value"] + jobs["tip"].fillna(0))',
      '''# Rule 2: never trust a manually entered total. Recompute always, and
# FLAG any row where the sheet disagrees. The previous version used the
# entered total when present and only fell back to recomputation, which is
# how the Dr Morral 8/7 tip drop reached metrics.json silently.
jobs["total_clean"] = jobs["job_value"].fillna(0) + jobs["tip"].fillna(0)
_mismatch = jobs["total"].notna() & (jobs["total"] != jobs["total_clean"])
if _mismatch.any():
    print(f"WARNING: {_mismatch.sum()} row(s) where the sheet total disagrees "
          f"with job_value + tip. Recomputed values are used:")
    print(jobs.loc[_mismatch, ["date", "customer", "job_value", "tip", "total",
                               "total_clean"]].to_string(index=False))''',
      "cr  analysis.py always recomputes total and flags mismatches")


if __name__ == "__main__":
    print("=" * 68)
    print("AUDIT FIXES")
    print("=" * 68)
    for label, status in FIXES:
        mark = {"FIXED": "[x]", "already applied": "[=]"}.get(status, "[ ]")
        print(f"  {mark} {label:<48} {status}")
    n = sum(1 for _, s in FIXES if s == "FIXED")
    print(f"\n  {n} applied. Backups written alongside each modified file.")
    print("\n  Now run:  python3 refresh.py && python3 part5_campaign_experiment.py")
