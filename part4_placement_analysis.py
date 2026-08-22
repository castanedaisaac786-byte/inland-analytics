"""
Part 4 — Placement Efficiency Analysis
=======================================
Tests whether cost per messaging conversation differs by Meta ad placement,
using permutation testing (same method as Parts 2 and 3).

MOTIVATING QUESTION
-------------------
After a campaign produced 28 messages and 0 bookings in 48 hours, the working
hypothesis was that cheap placements (Reels, Stories) were generating
accidental-tap messages that never convert. Reels and Stories were excluded
from all campaigns on that hunch. This script tests the hunch.

WHAT THIS CAN AND CANNOT ANSWER
-------------------------------
CAN:    Does cost per message differ by placement, beyond chance?
CANNOT: Does lead QUALITY differ by placement?

The Meta placement export contains spend, impressions, and messages. It
contains no booking outcomes. So this is a cost analysis, not a conversion
analysis — the same distinction that separated Section 4 from Section 6 in
Part 2, where a real cost-per-message gap by gender (p~0.0005) failed to
carry through into bookings (p~1.0).

A placement that produces cheap messages could be efficient OR could be
producing junk. This dataset cannot tell those apart. Resolving it requires
logging placement on every booked job.

METHOD NOTES
------------
- Rows with spend but no messaging results are INCLUDED with msgs=0. Dropping
  them would overstate efficiency for placements that burned spend for nothing
  — the same filtering error that inflated a campaign gap to 18.6x in Part 2.
- Rows with zero spend are excluded (2 messages are attributed to zero-spend
  rows; they cannot contribute to a cost ratio).
- Unit of randomization is the day x ad x placement row, matching the
  granularity Meta reports at.

Run:  python3 part4_placement_analysis.py
"""

import pandas as pd
import numpy as np

RNG = np.random.default_rng(42)
N_RESAMPLES = 10_000
REPORT = "data/placement_report.xlsx"   # Meta Ads Manager placement export

FEED    = ["Feed", "Facebook profile feed", "Threads feed"]
REELS   = ["Instagram Reels", "Facebook Reels", "Ads on Facebook Reels", "In-stream reels"]
STORIES = ["Instagram Stories", "Facebook Stories"]


def load(path=REPORT):
    df = pd.read_excel(path)
    df["msgs"] = np.where(
        df["Result type"].eq("Messaging conversations started"), df["Results"], 0
    ).astype(float)
    df["spend"] = df["Amount spent (USD)"].astype(float)
    df["imps"] = df["Impressions"].astype(float)
    return df[df.spend > 0].copy()


def summarize(df):
    g = (df.groupby("Placement")
           .agg(rows=("spend", "size"), spend=("spend", "sum"),
                msgs=("msgs", "sum"), imps=("imps", "sum"))
           .reset_index())
    g["cost_per_msg"] = np.where(g.msgs > 0, g.spend / g.msgs, np.nan)
    g["msgs_per_1k"] = g.msgs / g.imps * 1000
    g["pct_spend"] = g.spend / g.spend.sum() * 100
    return g.sort_values("spend", ascending=False)


def _gap(sub, a_name, b_name):
    """Aggregate cost-per-message difference between two label groups."""
    A, B = sub[sub.grp == a_name], sub[sub.grp == b_name]
    if A.msgs.sum() == 0 or B.msgs.sum() == 0:
        return np.nan
    return A.spend.sum() / A.msgs.sum() - B.spend.sum() / B.msgs.sum()


def permutation_test(df, a_list, b_list, a_name, b_name, n=N_RESAMPLES):
    """Two-sided permutation test on aggregate cost per message."""
    sub = df[df.Placement.isin(a_list + b_list)].copy()
    sub["grp"] = np.where(sub.Placement.isin(a_list), a_name, b_name)

    observed = _gap(sub, a_name, b_name)
    labels = sub.grp.values.copy()

    null = np.empty(n)
    for i in range(n):
        sub["grp"] = RNG.permutation(labels)
        null[i] = _gap(sub, a_name, b_name)
    null = null[~np.isnan(null)]

    p = (np.abs(null) >= abs(observed)).mean()

    A = sub[sub.Placement.isin(a_list)]
    B = sub[sub.Placement.isin(b_list)]
    print(f"\n{a_name} vs {b_name}")
    print(f"  {a_name:<9} ${A.spend.sum():8.2f} / {A.msgs.sum():4.0f} msgs = "
          f"${A.spend.sum()/A.msgs.sum():.2f}/msg")
    print(f"  {b_name:<9} ${B.spend.sum():8.2f} / {B.msgs.sum():4.0f} msgs = "
          f"${B.spend.sum()/B.msgs.sum():.2f}/msg")
    print(f"  observed gap ${observed:+.2f}   p = {p:.4f}   "
          f"({len(null):,} valid resamples)")
    return {"a": a_name, "b": b_name, "observed": observed, "p": p}


if __name__ == "__main__":
    df = load()
    print(f"Window: {df['Day'].min()} -> {df['Day'].max()}")
    print(f"Spend ${df.spend.sum():.2f} | {df.msgs.sum():.0f} messages | "
          f"{df.imps.sum():.0f} impressions | {len(df)} rows\n")

    print(summarize(df).to_string(index=False))

    results = [
        permutation_test(df, FEED, REELS, "FEED", "REELS"),
        permutation_test(df, FEED, STORIES, "FEED", "STORIES"),
        permutation_test(df, REELS, STORIES, "REELS", "STORIES"),
    ]

    print("\n" + "=" * 62)
    print("READ THIS BEFORE ACTING ON THE ABOVE")
    print("=" * 62)
    print("These are COST results, not QUALITY results. A placement that")
    print("produces cheap messages may still produce no bookings. Part 2")
    print("Section 6 is the cautionary case: a real cost gap by gender")
    print("(p~0.0005) did not carry through into who actually booked (p~1.0).")
    print()
    print("To answer the quality question, log the source placement on every")
    print("booked job, then rerun this comparing bookings-per-placement rather")
    print("than cost-per-message.")
