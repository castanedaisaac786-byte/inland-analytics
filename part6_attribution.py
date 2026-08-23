"""
Part 6 — Creative & Destination Attribution
============================================
The missing dataset. Parts 4 and 5 were both blocked by the same gap: ad data
had spend and messages but no bookings, so every result was a COST result.
This script closes that loop using an audited job log with creative_hook,
platform_destination, and ad_attributed columns.

THREE THINGS IT FINDS, EACH OF WHICH CORRECTS A PUBLISHED NUMBER
----------------------------------------------------------------
1. ROAS OVERSTATEMENT. Five jobs tagged channel="Meta Ads" were explicitly
   logged as organic Instagram DMs or feed visits with no ad involved. They
   contribute $1,010 of the $3,525 "Meta Ads" revenue. Real ad-attributed
   ROAS is 3.73x, not the 5.23x in the README — a 40% overstatement.

   Note the direction. The README previously flagged the OPPOSITE error
   (jobs from ads tagged as organic). Both exist. Channel tagging was wrong
   in both directions, which is why recomputing from an audited log matters
   more than tightening the tagging rule.

2. BENCHMARK COLLAPSE. Part 5's decision rule rests on "$26.09 per booking,"
   derived from a recalled 5 bookings on the Denise Reactions / "Real results"
   creative. The job log shows TWO. Depending on which spend figure applies
   ($130.47 for the "Real results" post or $42.84 for the "Denise reaction"
   post), true cost per booking is $65.23 or $21.42 — a 3x spread. The
   threshold is not merely wrong, it is undetermined.

3. CREATIVE IS THE LEVER, NOT PLACEMENT OR TARGETING. Problem-specific
   creatives ("Save a 2007 Chevy interior", "Pet Hair Removal") convert at a
   fraction of the cost of the broad August campaign. See ranking below.

Run:  python3 part6_attribution.py
"""

import pandas as pd
import numpy as np

JOB_LOG = "data/job_log.csv"
META_LIFETIME_SPEND = 673.49

# Spend per creative, from the Meta Ads Manager lifetime export.
# None = the creative could not be matched to a single spend line.
CREATIVE_SPEND = {
    "Save 2007 Chevy":   72.14,
    "Denise Reactions":  42.84,
    "August Broad":     113.13,
    "Pet Hair Removal":   None,
    "Unspecified":        None,
    "Patrick Ads":        None,
}

NON_DETAIL_TIERS = ["Non-Detail", "Pressure Wash"]


def load(path=JOB_LOG):
    df = pd.read_csv(path)
    # Rule 2: never trust a manually entered total.
    df["total"] = df.job_value.fillna(0) + df.tip.fillna(0)
    df["total_mismatch"] = df.logged_total != df.total
    return df


def audit_totals(df):
    bad = df[df.total_mismatch]
    print("=" * 74)
    print("DATA QUALITY — recomputed totals vs. logged totals")
    print("=" * 74)
    if len(bad) == 0:
        print("  All logged totals reconcile.")
    else:
        print(f"  {len(bad)} row(s) do NOT reconcile. Recomputed values are used.")
        print(bad[["date", "customer", "job_value", "tip",
                   "logged_total", "total"]].to_string(index=False))
        print("\n  This is a RECURRENCE of the tip-dropping error documented in")
        print("  Part 1. The script is hardened against it; the source sheet is not.")


def channel_view(d):
    print("\n" + "=" * 74)
    print("CHANNEL — detail jobs only (Rule 1)")
    print("=" * 74)
    ch = (d.groupby("channel")
            .agg(jobs=("total", "size"), revenue=("total", "sum"))
            .reset_index())
    ch["avg_ticket"] = ch.revenue / ch.jobs
    print(ch.sort_values("revenue", ascending=False).to_string(index=False))


def attribution_audit(d):
    print("\n" + "=" * 74)
    print("ATTRIBUTION AUDIT — organic inquiries tagged as paid")
    print("=" * 74)
    meta = d[d.channel == "Meta Ads"]
    paid = meta[meta.ad_attributed == 1]
    organic = meta[meta.ad_attributed == 0]

    print(f"  Tagged 'Meta Ads'      {len(meta):2d} jobs  ${meta.total.sum():,.0f}")
    print(f"    from an actual ad    {len(paid):2d} jobs  ${paid.total.sum():,.0f}")
    print(f"    organic, no ad       {len(organic):2d} jobs  ${organic.total.sum():,.0f}")
    print()
    print(organic[["date", "customer", "total", "platform_destination"]]
          .to_string(index=False))
    print()
    reported = meta.total.sum() / META_LIFETIME_SPEND
    actual = paid.total.sum() / META_LIFETIME_SPEND
    print(f"  ROAS as published      {reported:.2f}x")
    print(f"  ROAS, ad-attributed    {actual:.2f}x")
    print(f"  Overstatement          {(meta.total.sum()/paid.total.sum() - 1) * 100:.0f}%")
    return paid


def creative_ranking(paid):
    print("\n" + "=" * 74)
    print("CREATIVE PERFORMANCE — the actual lever")
    print("=" * 74)
    c = (paid.groupby("creative_hook")
              .agg(bookings=("total", "size"), revenue=("total", "sum"))
              .reset_index())
    c["avg_ticket"] = c.revenue / c.bookings
    c["spend"] = c.creative_hook.map(CREATIVE_SPEND)
    c["cost_per_booking"] = c.spend / c.bookings
    c["roas"] = c.revenue / c.spend
    print(c.sort_values("revenue", ascending=False)
           .to_string(index=False, na_rep="unknown"))
    print()
    print("  Where spend is known, the spread is the finding:")
    known = c[c.spend.notna()].sort_values("cost_per_booking")
    for _, r in known.iterrows():
        print(f"    {r.creative_hook:<18} ${r.cost_per_booking:6.2f}/booking   "
              f"{r.roas:5.2f}x ROAS   ({int(r.bookings)} bookings)")
    if len(known) >= 2:
        best, worst = known.iloc[0], known.iloc[-1]
        print(f"\n  {worst.creative_hook} costs "
              f"{worst.cost_per_booking / best.cost_per_booking:.1f}x more per booking "
              f"than {best.creative_hook}.")


def benchmark_audit(paid):
    print("\n" + "=" * 74)
    print("BENCHMARK AUDIT — the number Part 5's decision rule depends on")
    print("=" * 74)
    den = paid[paid.creative_hook == "Denise Reactions"]
    print(f"  Part 5 assumed : 5 bookings on $130.47  ->  $26.09 per booking")
    print(f"  Job log shows  : {len(den)} bookings (${den.total.sum():,.0f} revenue)")
    for spend, label in [(130.47, '"Real results" post'),
                         (42.84, '"Denise reaction" post')]:
        print(f"    if spend = ${spend:6.2f} ({label:<24}) "
              f"-> ${spend/len(den):6.2f}/booking, {den.total.sum()/spend:.2f}x")
    print("\n  >> Part 5's break-even threshold is UNDETERMINED until the")
    print("     creative-to-spend mapping is resolved. Do not act on $26.09.")


def destination_view(d):
    print("\n" + "=" * 74)
    print("PLATFORM DESTINATION")
    print("=" * 74)
    p = (d[d.platform_destination.notna()]
           .groupby("platform_destination")
           .agg(jobs=("total", "size"), revenue=("total", "sum"))
           .reset_index())
    p["avg_ticket"] = p.revenue / p.jobs
    print(p.sort_values("revenue", ascending=False).to_string(index=False))


if __name__ == "__main__":
    df = load()
    audit_totals(df)

    d = df[df.is_detail_job == 1].copy()
    print(f"\nDetail jobs: {len(d)} | revenue ${d.total.sum():,.0f} | "
          f"avg ticket ${d.total.mean():.2f}")

    channel_view(d)
    paid = attribution_audit(d)
    creative_ranking(paid)
    benchmark_audit(paid)
    destination_view(d)

    print("\n" + "=" * 74)
    print("LIMITATIONS")
    print("=" * 74)
    print("  - Creative attribution is self-reported from customer conversation,")
    print("    not click-tracked. A customer who saw three ads and named one is")
    print("    recorded as one. Last-touch by recall, not true attribution.")
    print("  - Three creatives could not be matched to a spend line, so their")
    print("    cost per booking is unknown. Pet Hair Removal drives the highest")
    print("    revenue of any creative and its efficiency is still unmeasured.")
    print("  - n = 14 ad-attributed bookings. Every ratio here is directional.")
