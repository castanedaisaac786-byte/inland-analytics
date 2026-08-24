"""
CORRECTION (Aug 24, 2026). The prior was built on 4 bookings at $18.04.
Click-level ad_id data shows only 2 of those 4 came from this creative --
BH is unverified and Maritza's lead carries the Denise ad_id. The real
prior is $72.14 / 2 = $36.07 per booking, exactly double the original.
The 95% interval widens from 9.4x to 29.8x ($9.99 - $297.84). The old
interim stop rule of $36 now sits AT the point estimate.

Part 7 — Scale-Up Validation (PRE-REGISTERED)
==============================================
Does a small-sample efficiency estimate survive a 4x increase in spend?

WHY THIS IS DIFFERENT FROM PARTS 2-6
------------------------------------
Every prior part in this repo is retrospective. Part 2 tested a demographic
split after the fact. Part 4 tested placements after the fact. Part 6 audited
attribution after the fact. Even Part 5, which is live, was designed after the
zero-booking problem had already appeared and carries four confounds.

Part 7 is the first analysis in the repo where the prediction is written down
BEFORE the money is spent. That is the whole point of it.

THE PRIOR
---------
Part 6 identified "Save a 2007 Chevy interior" as the best-performing creative
in the account: $72.14 spend, 4 bookings, $36.07 per booking, 8.18x ROAS.

That estimate rests on FOUR events. The honest 95% interval on a Poisson count
of 4 runs from 1.09 to 10.24, which puts true cost per booking somewhere
between $7.04 and $66.19 — a spread of nearly 10x. The point estimate is the
middle of a very wide range, not a measurement.

This part exists because acting on a four-event estimate without saying out
loud how uncertain it is would be the exact failure mode Part 2 Section 6 and
Part 3 were written to avoid.

THE TEST
--------
Scale to $40/day. Staged, with an interim decision at $120.

  Stage 1 (days 1-3, $120): does $36.07/booking hold at 1.7x the original spend?
  Interim rule: if observed cost per booking exceeds $36 (2x the prior point
                estimate), stop and re-evaluate rather than deploying the rest.
  Stage 2 (days 4-7, $160): only if Stage 1 clears.

TWO HYPOTHESES, BOTH PRE-REGISTERED
-----------------------------------
H1 (validation):  Observed cost per booking at scale falls inside the prior
                  95% interval of [$7.04, $66.19].
                  -> Failure to reject means the creative generalizes.

H2 (saturation):  Cost per booking is HIGHER in days 4-7 than in days 1-3,
                  because the cheapest reachable audience is exhausted first.
                  -> Directional prediction made in advance. Tested by
                     permutation on daily data (same method as Parts 3 and 4).

CAPACITY CONSTRAINT — recorded because it may bind before the ads do
--------------------------------------------------------------------
Historical throughput is 3.6 detail jobs/week (29 jobs / ~8 weeks). The point
prediction at $280 is 15.5 bookings, which is 4.3x that rate. If bookings are
declined, delayed, or rushed because of capacity rather than demand, the
measured conversion rate understates the creative and OVERSTATES cost per
booking. Log every declined or delayed booking or this experiment is invalid.

Run:  python3 part7_scaleup_test.py
"""

import numpy as np
import pandas as pd
from scipy import stats

RNG = np.random.default_rng(42)
N_RESAMPLES = 10_000

# ---------------------------------------------------------------------------
# PRIOR — from Part 6, locked before spend
# ---------------------------------------------------------------------------
PRIOR = {
    "creative":   "Save a 2007 Chevy interior",
    "spend":      72.14,
    "bookings":   4,
    "avg_ticket": 147.50,
}
PRIOR["cost_per_booking"] = PRIOR["spend"] / PRIOR["bookings"]

# ---------------------------------------------------------------------------
# PLAN — locked before spend
# ---------------------------------------------------------------------------
PLAN = {
    "daily_budget":     40.00,
    "stage1_days":      3,
    "stage2_days":      4,
    "interim_stop_cpb": 54.00,   # 2x the prior point estimate
    "capacity_ceiling": 3.6,     # historical detail jobs per week
}
PLAN["stage1_spend"] = PLAN["daily_budget"] * PLAN["stage1_days"]
PLAN["stage2_spend"] = PLAN["daily_budget"] * PLAN["stage2_days"]
PLAN["total_spend"]  = PLAN["stage1_spend"] + PLAN["stage2_spend"]


def poisson_interval(count, exposure, alpha=0.05):
    """Exact 95% interval on a Poisson rate, given `count` events."""
    lo = stats.chi2.ppf(alpha / 2, 2 * count) / 2 if count > 0 else 0.0
    hi = stats.chi2.ppf(1 - alpha / 2, 2 * (count + 1)) / 2
    return lo / exposure, hi / exposure


def prior_interval():
    lo_rate, hi_rate = poisson_interval(PRIOR["bookings"], PRIOR["spend"])
    return 1 / hi_rate, 1 / lo_rate      # cost per booking: low, high


def predict(spend):
    cpb_lo, cpb_hi = prior_interval()
    return {
        "point":   spend / PRIOR["cost_per_booking"],
        "low":     spend / cpb_hi,
        "high":    spend / cpb_lo,
    }


def preregister():
    cpb_lo, cpb_hi = prior_interval()
    print("=" * 74)
    print("PART 7 — PRE-REGISTRATION  (write this down BEFORE launching)")
    print("=" * 74)
    print(f"\nCreative: {PRIOR['creative']}")
    print(f"  prior: ${PRIOR['spend']:.2f} -> {PRIOR['bookings']} bookings "
          f"= ${PRIOR['cost_per_booking']:.2f}/booking")
    print(f"  95% interval on cost per booking: ${cpb_lo:.2f} to ${cpb_hi:.2f}")
    print(f"  >> the point estimate rests on {PRIOR['bookings']} events. "
          f"The interval spans {cpb_hi/cpb_lo:.1f}x.")

    print(f"\nPlan: ${PLAN['daily_budget']:.0f}/day, staged")
    for label, spend in [("Stage 1 (days 1-3)", PLAN["stage1_spend"]),
                         ("Full run  (days 1-7)", PLAN["total_spend"])]:
        p = predict(spend)
        print(f"  {label}  ${spend:6.2f}")
        print(f"      point prediction {p['point']:5.1f} bookings   "
              f"95% range {p['low']:.1f} to {p['high']:.1f}")
        print(f"      revenue          ${p['point']*PRIOR['avg_ticket']:7.0f}   "
              f"range ${p['low']*PRIOR['avg_ticket']:.0f} to "
              f"${p['high']*PRIOR['avg_ticket']:.0f}")

    print(f"\nInterim stop rule: if Stage 1 cost per booking > "
          f"${PLAN['interim_stop_cpb']:.2f}, halt and re-evaluate.")
    print(f"Capacity ceiling:  {PLAN['capacity_ceiling']:.1f} jobs/week historical. "
          f"Point prediction is {predict(PLAN['total_spend'])['point']:.1f}.")
    print(f"  >> capacity may bind before spend does. Log declined/delayed jobs.")


def evaluate(observed_spend, observed_bookings, observed_revenue=None):
    """H1: does the scaled result fall inside the prior interval?"""
    cpb_lo, cpb_hi = prior_interval()
    obs_cpb = observed_spend / observed_bookings if observed_bookings else np.inf

    print("\n" + "=" * 74)
    print("H1 — VALIDATION")
    print("=" * 74)
    print(f"  observed: ${observed_spend:.2f} -> {observed_bookings} bookings "
          f"= ${obs_cpb:.2f}/booking")
    print(f"  prior 95% interval: ${cpb_lo:.2f} to ${cpb_hi:.2f}")
    inside = cpb_lo <= obs_cpb <= cpb_hi
    print(f"  result: {'INSIDE — creative generalizes' if inside else 'OUTSIDE — prior does not hold at scale'}")
    if observed_revenue:
        print(f"  ROAS: {observed_revenue/observed_spend:.2f}x")
    return inside


def saturation_test(daily, n=N_RESAMPLES):
    """
    H2: is cost per booking higher in the back half than the front half?
    `daily` = DataFrame with columns [day, spend, bookings].
    """
    daily = daily.copy()
    mid = len(daily) // 2
    daily["half"] = ["early"] * mid + ["late"] * (len(daily) - mid)

    def gap(d):
        e, l = d[d.half == "early"], d[d.half == "late"]
        if e.bookings.sum() == 0 or l.bookings.sum() == 0:
            return np.nan
        return l.spend.sum() / l.bookings.sum() - e.spend.sum() / e.bookings.sum()

    observed = gap(daily)
    labels = daily.half.values.copy()
    null = np.empty(n)
    for i in range(n):
        daily["half"] = RNG.permutation(labels)
        null[i] = gap(daily)
    null = null[~np.isnan(null)]
    p = (null >= observed).mean()      # one-sided: predicted direction is UP

    print("\n" + "=" * 74)
    print("H2 — AUDIENCE SATURATION")
    print("=" * 74)
    print(f"  observed late-minus-early cost per booking: ${observed:+.2f}")
    print(f"  one-sided p = {p:.4f}  ({len(null):,} valid resamples)")
    print("  prediction was that cost RISES as the cheap audience is exhausted.")
    return p


if __name__ == "__main__":
    preregister()

    print("\n" + "=" * 74)
    print("RESULTS — fill in after the run")
    print("=" * 74)
    print("  evaluate(observed_spend=280, observed_bookings=?, observed_revenue=?)")
    print("  saturation_test(pd.DataFrame({'day':[1..7],'spend':[...],'bookings':[...]}))")
    print("\n  Required logging: creative_hook, campaign_arm, and placement on")
    print("  EVERY booking, plus a row for every declined or delayed job.")
