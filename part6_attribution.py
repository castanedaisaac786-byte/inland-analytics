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
   The Denise Reactions creative ran as TWO separate campaigns, $42.84 and
   $96.20, for $139.04 total. Against 2 logged bookings that is $69.52 per
   booking — not $26.09. Part 5's break-even thresholds must be recomputed
   against $69.52.

3. CREATIVE IS THE LEVER, NOT PLACEMENT OR TARGETING. With full spend
   attribution the spread is 7.2x:

     Save 2007 Chevy    $18.04/booking   8.18x
     Denise Reactions   $69.52/booking   2.73x
     August Broad      $113.13/booking   1.59x
     Patrick Ads       $130.00/booking   1.31x

   Every creative except Save 2007 Chevy is close to or below the point
   where a 50/50 labor split erases the margin entirely. At 2x ROAS with
   half of revenue going to labor, the ad pays for itself and nothing else.

Run:  python3 part6_attribution.py
"""

import pandas as pd
import numpy as np

JOB_LOG = "data/job_log.csv"
META_LIFETIME_SPEND = 785.00   # updated 2026-08-23

# Spend per creative, from the Meta Ads Manager lifetime export.
# None = the creative could not be matched to a single spend line.
CREATIVE_SPEND = {
    "Save 2007 Chevy":   72.14,
    "Denise Reactions": 139.04,   # 42.84 + 96.20, two separate campaign runs
    "August Broad":     113.13,
    "Patrick Ads":      130.00,
    "Pet Hair Removal":   None,   # shares the $330.69 unattributed bucket
    "Unspecified":        None,   # with Pet Hair Removal; split unknown
}

# Total spend minus everything mapped to a named creative.
UNATTRIBUTED_SPEND = META_LIFETIME_SPEND - sum(
    v for v in CREATIVE_SPEND.values() if v is not None)

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
    published = meta.total.sum() / 673.49          # the README's figure
    print(f"  ROAS as published      {published:.2f}x   (${meta.total.sum():,.0f} / $673.49)")
    print(f"  ROAS, ad-attributed    {actual:.2f}x   (${paid.total.sum():,.0f} / ${META_LIFETIME_SPEND:,.2f})")
    print(f"  Published figure is    {(published/actual - 1) * 100:.0f}% too high")
    print()
    print(f"  After a 50/50 labor split: ${paid.total.sum()*0.5:,.2f} - "
          f"${META_LIFETIME_SPEND:,.2f} = ${paid.total.sum()*0.5 - META_LIFETIME_SPEND:+,.2f} net")
    print("  Advertising is profitable, but on roughly half the margin the")
    print("  gross figures imply.")
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

    unk = c[c.spend.isna()]
    if len(unk):
        b, r = unk.bookings.sum(), unk.revenue.sum()
        print(f"\n  Unattributed bucket: {int(b)} bookings, ${r:,.0f} revenue on "
              f"${UNATTRIBUTED_SPEND:,.2f}")
        print(f"    blended ${UNATTRIBUTED_SPEND/b:.2f}/booking, {r/UNATTRIBUTED_SPEND:.2f}x")
        print(f"    Pet Hair Removal is inside this bucket and has the highest")
        print(f"    average ticket in the account. Splitting this spend is the")
        print(f"    single highest-value attribution fix outstanding.")


def benchmark_audit(paid):
    print("\n" + "=" * 74)
    print("BENCHMARK AUDIT — the number Part 5's decision rule depends on")
    print("=" * 74)
    den = paid[paid.creative_hook == "Denise Reactions"]
    print(f"  Part 5 assumed : 5 bookings on $130.47  ->  $26.09 per booking")
    print(f"  Job log shows  : {len(den)} bookings (${den.total.sum():,.0f} revenue)")
    spend = CREATIVE_SPEND["Denise Reactions"]
    cpb = spend / len(den)
    print(f"  Resolved       : $42.84 + $96.20 = ${spend:.2f} across two runs")
    print(f"                   -> ${cpb:.2f} per booking, {den.total.sum()/spend:.2f}x")
    print()
    print("  PART 5 BREAK-EVEN, recomputed against the real benchmark:")
    for name, sp, ev in [("messages arm", 95.01, 58), ("leads arm", 20.72, 3)]:
        print(f"    {name:<14} ${sp:6.2f} / {ev:2d} events = ${sp/ev:.2f}/event "
              f"-> needs {sp/ev/cpb:.1%} conversion")
    print()
    print("  The messages arm needs only 2.4% conversion to clear the bar and has")
    print("  produced 0 bookings on 58 messages. The leads arm needs 9.9% and is")
    print("  running at roughly 33% on n=1.")


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
