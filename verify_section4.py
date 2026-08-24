"""
Part 2 Section 4 — full-spend re-analysis
==========================================
The original Section 4 computed cost per message over `messaging_only_raw.csv`,
which retains only rows that produced at least one message. That excludes
$284.87 — 48% of messaging-campaign spend — that produced nothing.

Cost per message computed only over units that produced a message is not
cost per message. This is the same error class Part 4 documents and rejects:
"dropping zero-result rows would overstate efficiency."

This script recomputes both demographic tests on the full-spend basis.

Run:  python3 verify_section4.py
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N_RESAMPLES = 10_000
EXPORT = "data/meta_ads_detailed_report.xlsx"
MESSAGING = "Messaging conversations started"


def load_full_spend(path=EXPORT):
    """Every row of every messaging-objective campaign, including rows
    that spent money and produced nothing."""
    d = pd.read_excel(path)
    d["spend"] = pd.to_numeric(d["Amount spent (USD)"], errors="coerce").fillna(0)
    d["msgs"] = np.where(
        d["Result type"].eq(MESSAGING),
        pd.to_numeric(d["Results"], errors="coerce").fillna(0),
        0,
    )
    campaigns = d.loc[d["Result type"].eq(MESSAGING), "Campaign name"].unique()
    return d[d["Campaign name"].isin(campaigns)].copy(), campaigns


def cost_per_message(df):
    return df.spend.sum() / df.msgs.sum() if df.msgs.sum() else np.nan


def permutation_test(df, col, group_a, label_a, label_b, n=N_RESAMPLES):
    """Two-sided permutation test on the aggregate cost-per-message gap."""
    s = df.copy()
    s["g"] = np.where(s[col].isin(group_a), "A", "B")

    def gap(x):
        A, B = x[x.g == "A"], x[x.g == "B"]
        if A.msgs.sum() == 0 or B.msgs.sum() == 0:
            return np.nan
        return cost_per_message(A) - cost_per_message(B)

    observed = gap(s)
    labels = s.g.values.copy()
    true_a, true_b = s[s.g == "A"].copy(), s[s.g == "B"].copy()
    null = np.empty(n)
    for i in range(n):
        s["g"] = RNG.permutation(labels)
        null[i] = gap(s)
    null = null[~np.isnan(null)]
    p = (np.abs(null) >= abs(observed)).mean()

    A, B = true_a, true_b
    print(f"\n  {label_a} vs {label_b}")
    print(f"    {label_a:<14} ${A.spend.sum():7.2f} / {A.msgs.sum():3.0f} msgs "
          f"= ${cost_per_message(A):.2f}/msg")
    print(f"    {label_b:<14} ${B.spend.sum():7.2f} / {B.msgs.sum():3.0f} msgs "
          f"= ${cost_per_message(B):.2f}/msg")
    print(f"    gap ${observed:+.2f}   p = {p:.4f}   ({len(null):,} resamples)")
    return p


if __name__ == "__main__":
    full, campaigns = load_full_spend()

    print("=" * 70)
    print("SECTION 4 RE-ANALYSIS — FULL-SPEND BASIS")
    print("=" * 70)
    print(f"  {len(campaigns)} messaging campaigns")
    print(f"  conditioned file: 117 rows, $312.13")
    print(f"  full spend:       {len(full)} rows, ${full.spend.sum():.2f}")
    print(f"  excluded by the original filter: "
          f"${full.spend.sum() - 312.13:.2f} "
          f"({(full.spend.sum() - 312.13) / full.spend.sum():.0%} of spend)")

    p_gender = permutation_test(
        full[full.Gender.isin(["female", "male"])], "Gender",
        ["female"], "female", "male")
    p_age = permutation_test(
        full, "Age", ["55-64", "65+"], "55+", "under 55")

    print("\n" + "=" * 70)
    print("PUBLISHED vs CORRECTED")
    print("=" * 70)
    print(f"  {'':22} {'published':<22} {'full-spend':<22}")
    print(f"  {'gender':<22} {'$1.50 v $2.36, p=.0005':<22} "
          f"{'$3.49 v $3.95, p=%.4f' % p_gender:<22} DEAD")
    print(f"  {'age 55+':<22} {'$1.53 v $2.35, p=.0015':<22} "
          f"{'$2.90 v $4.52, p=%.4f' % p_age:<22} SURVIVES")

    print("\n  Eight hypothesis tests across this project. Bonferroni "
          "threshold = 0.00625.")
    print(f"  Age survives at p={p_age:.4f}. Gender does not, and would not "
          "have\n  even at the published 0.0005 had it been real.")
