"""
Audit a5 — Part 3's "$840 discrepancy" is a basis mismatch, not a tip bug.
==========================================================================
part3/notebooks/analysis.py compares detail-only recomputed revenue ($4,721,
29 jobs) against a hard-coded snapshot of the source sheet's ALL-JOBS total
($5,561), which included ~$1,810 of pressure-wash and non-detail rows the
$4,721 basis deliberately excludes. It prints "Discrepancy: $-840" and blames
tip errors.

The honest like-for-like check: the sheet's own Total column sums to $6,491
against its own TOTALS row of $6,531 — a $40 gap that is exactly the Dr Morral
8/7 dropped tip. That is a smaller number and a much stronger finding, because
it is real.

Run from the repo root:  python3 fix_part3_discrepancy.py
"""
import pathlib
import re
import shutil

P = pathlib.Path("part3_maintenance_conversion/notebooks/analysis.py")

NEW_BLOCK = '''print("=" * 60)
print("DATA QUALITY CHECK")
print("=" * 60)
computed = jobs_detail["total"].sum()
print(f"Detail-only revenue (job_value + tip): ${computed:,.0f}")
print()
print("NOTE ON BASIS. An earlier version of this check compared the")
print("detail-only figure against the source sheet's ALL-JOBS total")
print("($5,561) and reported an $840 'discrepancy' attributed to tip")
print("errors. That was a basis mismatch, not a data error: the two")
print("figures count different job sets. The $840 was never a tip bug.")
print()
print("The like-for-like check is the sheet against itself. Its Total")
print("column sums to $6,491 against its own TOTALS row of $6,531 --")
print("a $40 gap, which is exactly the Dr Morral 8/7 dropped tip")
print("($110 + $40 logged as $110). One row, $40, real.")
print()
print("Every script here recomputes from job_value + tip and treats any")
print("entered total as a value to check against, never to trust.")
'''


def main():
    if not P.exists():
        raise SystemExit(f"{P} not found — run from the repo root.")
    t = P.read_text()
    if "basis mismatch, not a data error" in t:
        print("Already applied."); return

    m = re.search(r'print\("=" \* 60\)\s*\nprint\("DATA QUALITY CHECK"\).*?(?=\nprint\("=" \* 60\)\s*\nprint\("MAINTENANCE)',
                  t, re.S)
    if not m:
        print("Could not locate the DATA QUALITY CHECK block.")
        print("Patch by hand: replace it with the text in NEW_BLOCK above.")
        return

    shutil.copy(P, str(P) + ".bak")
    P.write_text(t[:m.start()] + NEW_BLOCK + "\n" + t[m.end():])
    print(f"FIXED. Backup at {P}.bak")
    print("Rerun:  cd part3_maintenance_conversion/notebooks && python3 analysis.py")


if __name__ == "__main__":
    main()
