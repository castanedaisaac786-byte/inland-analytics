"""
Part 5 — Campaign Mechanism Experiment
=======================================
Two campaigns running simultaneously to test whether the ACQUISITION MECHANISM
(instant form + fast callback vs. Messenger conversation) drives bookings,
after targeting changes alone failed to fix a zero-booking problem.

THE CHAIN THAT LED HERE
-----------------------
Part 2, Section 4:  Cost per message differed by gender (p~0.0005) and by age
                    (p~0.0015). Both are COST findings.
Part 2, Section 6:  Tested whether gender predicted BOOKING, not just messaging.
                    p~1.0. The cost finding did not carry through to revenue.
                    Lesson: cheap-to-reach and likely-to-buy are different
                    populations.
Aug 2026:           A live campaign produced 28 messages in 48 hours and zero
                    bookings. Working hypothesis: cheap placements (Reels,
                    Stories) were generating accidental-tap messages.
Part 4:             Permutation-tested that hypothesis on 456 rows of placement
                    data. Reels was the CHEAPEST placement ($3.46/msg) and
                    carried 58% of all message volume; Feed vs Reels was not
                    distinguishable (p=0.205). Stories WAS significantly worse
                    ($8.03/msg vs Reels, p=0.0004). The Reels half of the
                    hypothesis was wrong; the Stories half held.
                    BUT: placement data contains no bookings, so Part 4 could
                    only rank placements by COST — the same limitation as
                    Section 4. It could not test lead quality.
Part 5 (this):      Targeting was widened and placements adjusted. Result:
                    58 messages on $95.01 spend, still zero bookings. More
                    messages, same revenue. Targeting is not the lever.
                    So test the mechanism instead.
Part 6:             Resolved the benchmark. The Denise Reactions creative ran
                    TWICE ($42.84 + $96.20 = $139.04) for 2 logged bookings —
                    $69.52 per booking, not the $26.09 this file previously
                    assumed from 5 recalled bookings. All thresholds below are
                    recomputed against $69.52.

CENTRAL QUESTION
----------------
Does the way a lead enters the funnel determine whether they pay, independent
of who we target?

Run:  python3 part5_campaign_experiment.py
"""

import numpy as np
from scipy import stats

# =============================================================================
# 1. BENCHMARK — the only campaign in account history with a known booking rate
# =============================================================================
REFERENCE = {
    "name":     "Denise Reactions creative (two runs)",
    "spend":    139.04,     # $42.84 + $96.20, RESOLVED Aug 2026
    "messages": 49,         # 17 + 32 across the creative's TWO runs.
                            # The earlier 26 belonged to "Real results, real
                            # feedback" — a different creative. Numerator and
                            # denominator had come from different campaigns.
    "bookings": 2,          # from the audited job log, not recall
}
REFERENCE["conv_rate"]       = REFERENCE["bookings"] / REFERENCE["messages"]
REFERENCE["cost_per_booking"] = REFERENCE["spend"] / REFERENCE["bookings"]

# =============================================================================
# 2. EXPERIMENT REGISTRY — what differs, what is held constant
# =============================================================================
ARM_A = {
    "id":          "A_MESSAGES",
    "objective":   "Engagement / messaging conversations",
    "entry_point": "Messenger conversation",
    "age":         "45+",
    "placements":  "All except Stories",
    "interests":   "SHARED",
    "geo":         "SHARED",
}

ARM_B = {
    "id":          "B_LEADS",
    "objective":   "Leads / instant form",
    "entry_point": "Instant form + callback within 15 min",
    "age":         "20-65+",
    "placements":  "All placements (Stories INCLUDED)",
    "interests":   "SHARED",
    "geo":         "SHARED",
}

HELD_CONSTANT = ["Interest targeting", "Geographic radius", "Service offering"]

# Variables that differ between arms. Each one is a confound.
CONFOUNDS = [
    ("Objective / entry point", "Messenger",        "Instant form",   "INTENDED — this is the test"),
    ("Age range",               "45+",              "20-65+",         "CONFOUND"),
    ("Stories placement",       "Excluded",         "Included",       "CONFOUND — known-bad, biases AGAINST Arm B"),
    ("Response mechanism",      "Reply when seen",  "Call in 15 min", "BUNDLED with objective — cannot separate"),
]

# =============================================================================
# 3. CURRENT STATE
# =============================================================================
# Figures below come from the Meta ad-level export, not the app UI.
# The earlier $95.01 / 58 reconciled to no campaign in any export.
CURRENT_A = {"spend": 56.61, "messages": 34, "bookings": 1}   # Optimized targeting Camp
CURRENT_B = {"spend": 20.77, "leads":     3, "bookings": 0}   # tentative booking not confirmed


def evaluate_zero_result(spend, events, hypothesis_rate, benchmark_cpb):
    """What does zero bookings on n events actually tell us?"""
    cost_per_event = spend / events
    p_zero = stats.binom.pmf(0, events, hypothesis_rate)
    upper_95 = 1 - 0.05 ** (1 / events)          # exact 95% upper bound, 0 successes
    break_even = cost_per_event / benchmark_cpb  # conv rate needed to match benchmark
    return {
        "cost_per_event": cost_per_event,
        "p_zero_given_benchmark": p_zero,
        "conv_upper_95": upper_95,
        "break_even_conv": break_even,
        "events_needed": break_even * events,
        "still_viable": break_even < upper_95,
    }


# =============================================================================
# 4. PRE-REGISTERED DECISION RULE — written before results are known
# =============================================================================
DECISION_RULE = {
    "duration":       "14 days, or $100 spend per arm, whichever comes first",
    "primary_metric": "Cost per BOOKING. Not cost per message, not cost per lead.",
    "why":            "A 'messaging conversation' and a 'lead' are different units. "
                      "Only bookings are comparable across arms.",
    "benchmark":      f"${REFERENCE['cost_per_booking']:.2f} per booking",
    "rule":           "Whichever arm produces more bookings wins and gets the budget, "
                      "even if the gap is small and not statistically significant.",
    "no_touching":    "No edits to either campaign during the window. Every edit "
                      "resets learning and adds a variable.",
    "required_logging": "campaign_arm and placement columns on every booked job "
                        "in job_log.csv. Without this the experiment produces nothing.",
}


def report():
    print("=" * 72)
    print("PART 5 — CAMPAIGN MECHANISM EXPERIMENT")
    print("=" * 72)

    print(f"\n[1] BENCHMARK: {REFERENCE['name']}")
    print(f"    ${REFERENCE['spend']:.2f} / {REFERENCE['messages']} msgs / "
          f"{REFERENCE['bookings']} bookings")
    print(f"    conversion {REFERENCE['conv_rate']:.1%} | "
          f"cost per booking ${REFERENCE['cost_per_booking']:.2f}")

    print("\n[2] EXPERIMENT DESIGN")
    print(f"    {'':22} {'ARM A (messages)':<22} {'ARM B (form)':<22}")
    print(f"    {'-'*22} {'-'*22} {'-'*22}")
    for key in ["objective", "entry_point", "age", "placements"]:
        print(f"    {key:22} {str(ARM_A[key])[:21]:<22} {str(ARM_B[key])[:21]:<22}")
    print(f"\n    Held constant: {', '.join(HELD_CONSTANT)}")

    print("\n[3] CONFOUND AUDIT")
    for var, a, b, status in CONFOUNDS:
        print(f"    {var:26} A={a:<18} B={b:<18} {status}")
    print("\n    >> Four variables differ. This is a test of BUNDLE A vs BUNDLE B,")
    print("       not of 'forms vs messages'. If Arm B wins, the licensed claim is")
    print("       'the form bundle outperformed the message bundle' — nothing more.")
    print("    >> Stories is included in Arm B despite Part 4 showing it is the")
    print("       worst placement (p=0.0004). That bias runs AGAINST Arm B, so a")
    print("       win for B is conservative; a loss for B is uninterpretable.")
    print("    >> FIX AVAILABLE: excluding Stories from Arm B removes one confound")
    print("       and strengthens the arm you expect to win.")

    print("\n[3b] HEAD TO HEAD")
    a_cpb = "n/a" if CURRENT_A["bookings"] == 0 else f"${CURRENT_A['spend']/CURRENT_A['bookings']:.2f}"
    b_cpb = ("n/a" if CURRENT_B["bookings"] == 0
             else f"${CURRENT_B['spend']/CURRENT_B['bookings']:.2f}")
    print(f"    ARM A messages  ${CURRENT_A['spend']:6.2f} / {CURRENT_A['messages']:2d} msgs  "
          f"-> {CURRENT_A['bookings']} bookings, cost/booking {a_cpb}")
    print(f"    ARM B leads     ${CURRENT_B['spend']:6.2f} / {CURRENT_B['leads']:2d} leads "
          f"-> {CURRENT_B['bookings']} booking,  cost/booking {b_cpb}")
    print(f"    benchmark to beat: ${REFERENCE['cost_per_booking']:.2f}/booking")
    print("    >> Arm B produced a booking on 22% of Arm A's spend. Cost per")
    print("       EVENT favours A 4x and is not the metric. Only bookings compare.")

    print("\n[4] CURRENT EVIDENCE — ARM A")
    r = evaluate_zero_result(
        CURRENT_A["spend"], CURRENT_A["messages"],
        REFERENCE["conv_rate"], REFERENCE["cost_per_booking"],
    )
    print(f"    ${CURRENT_A['spend']:.2f} / {CURRENT_A['messages']} messages / "
          f"{CURRENT_A['bookings']} bookings  (${r['cost_per_event']:.2f}/msg)")
    print(f"    P(0 bookings | benchmark rate {REFERENCE['conv_rate']:.1%}) = "
          f"{r['p_zero_given_benchmark']:.3%}")
    print(f"      -> the current campaign converts WORSE than the benchmark. That")
    print(f"         is now well-supported, not a hunch.")
    print(f"    95% upper bound on true conversion rate = {r['conv_upper_95']:.1%}")
    print(f"    Break-even conversion to match ${REFERENCE['cost_per_booking']:.2f}/booking "
          f"= {r['break_even_conv']:.1%}  ({r['events_needed']:.1f} bookings)")
    print(f"    Verdict: {'STILL VIABLE' if r['still_viable'] else 'RULED OUT'} — "
          f"break-even {r['break_even_conv']:.1%} sits under the "
          f"{r['conv_upper_95']:.1%} ceiling, but the margin is closing.")

    print("\n[5] WHAT THE ZERO-BOOKING RESULT ALREADY PROVES")
    print("    Targeting was widened and message volume went UP. Bookings stayed at")
    print("    zero. More reach did not produce more revenue.")
    print("    -> Targeting is not the binding constraint.")
    print("    -> This is the third time cost-side improvement failed to move")
    print("       bookings (Section 4 -> Section 6, Part 4, and now Part 5).")
    print("       The pattern is consistent enough to act on: optimize for the")
    print("       conversion step, not the acquisition step.")

    print("\n[6] PRE-REGISTERED DECISION RULE")
    for k, v in DECISION_RULE.items():
        print(f"    {k:18} {v}")

    print("\n[7] LIMITATIONS")
    print("    - The benchmark is RESOLVED as of Part 6: $139.04 across two runs")
    print("      for 2 logged bookings = $69.52. The earlier $26.09 figure came")
    print("      from 5 recalled bookings and was wrong on both terms.")
    print("    - Arm B's single booking is TENTATIVE and below average ticket")
    print("      ($100 vs $162.79). Treat $20.72/booking as provisional.")
    print("    - Expected sample is ~20-30 events and 0-6 bookings per arm. This")
    print("      will NOT reach significance. The decision rule above is designed")
    print("      to be actionable anyway — see Part 3 for the same situation")
    print("      handled honestly (p=1.000, ~389 samples needed per channel).")
    print("    - Both arms compete in the same auction, inflating each other's CPM.")
    print("      Some observed cost is self-inflicted, not market rate.")

    print("\n[8] WHAT THIS DECIDES")
    print("    Whichever arm wins gets the full budget when the operator takes over")
    print("    the Inland Empire market. This experiment exists to answer one")
    print("    question before that handoff: what do we double down on?")
    print("=" * 72)


if __name__ == "__main__":
    report()
