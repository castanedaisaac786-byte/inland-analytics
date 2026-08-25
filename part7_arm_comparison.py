"""
Part 7 - Mechanism Comparison at Unequal Budget (PRE-REGISTERED)
Registered 2026-08-24, before the outcome is known.

REPLACES the original Part 7, which pre-registered a scale-up of "Save a 2007
Chevy interior" on a prior of $18.04/booking from 4 events. Click-level ad_id
data later showed only 2 of those 4 carried that ad's ID. True prior is
$72.14/2 = $36.07, and the 95% interval widens from 9.4x to 29.8x. The
creative also stopped delivering 2026-07-20. That test was never run; it
survives in git history as a pre-registration invalidated by better data.

THE QUESTION: does an instant lead form convert as well as a Messenger
conversation, per dollar?
  ARM A messages  Optimized targeting Camp - Copy, ad "Any time - Copy", $20/day
  ARM B form      B Leads Test, instant form + callback, $5/day

NOT A CLEAN A/B TEST
1. Budgets are 4:1. Only cost per booking compares; raw counts do not.
2. The budget split is itself a confound - Meta's optimizer behaves
   differently at $5/day, and a low-budget campaign may never leave the
   learning phase. That handicap is inseparable from the mechanism.
3. Objective, entry point, and response speed all differ. Bundle vs bundle.
4. Allocation is not random. The bigger budget went to the arm already
   believed better. This is a rollout with a hedge, not an experiment.

PRIOR (lifetime, click-attributed)
  messages  $74.99 -> 2 bookings, $37.49 each
  form     $101.81 -> 0 bookings, never converted
The form mechanism has spent MORE than messages and produced nothing. That
predates this test and is the strongest evidence in it.

POWER. At $5/day for 14 days Arm B spends $70. If it converted at exactly the
messages rate it would expect 1.87 bookings and STILL show zero 15.5% of the
time. A zero from Arm B is weak evidence. Arm A expects 7.47 and shows zero
0.1% of the time.

DECISION RULE
  duration       14 days from 2026-08-24, or $280 on Arm A
  primary metric cost per BOOKING, not per lead or message
  minimum sample Arm B is NOT judged before $112 cumulative spend
  win            lower cost per booking takes the budget, significance or not
  tie            Arm B at $112 with 0 bookings while Arm A has 3+ retires forms
  no touching    no creative, budget, audience or placement edits in the window

WHAT WOULD CHANGE MY MIND: two form bookings inside $70 puts Arm B at
$35/booking, indistinguishable from Arm A. Four leads arrived; all four went
unresponsive.

"""
import numpy as np
from scipy import stats
""
REGISTERED = "2026-08-24"
MIN_SPEND_TO_JUDGE_B = 112.0
DAYS = 14
PRIOR = {"messages": {"spend": 74.99, "bookings": 2, "revenue": 425.0}, "form": {"spend": 101.81, "bookings": 0, "revenue": 0.0}}
ARMS = {"A_messages": {"campaign": "Optimized targeting Camp - Copy", "daily": 20.0, "spend": 18.38, "events": 3, "bookings": 1, "revenue": 300.0}, "B_form": {"campaign": "B Leads Test", "daily": 5.0, "spend": 50.76, "events": 4, "bookings": 0, "revenue": 0.0}}



def poisson_hi(n, exposure, conf=0.95):
    return stats.chi2.ppf(conf if n == 0 else 1 - (1 - conf) / 2,
                          2 * n + 2) / 2 / exposure


def cpb(a):
    return a["spend"] / a["bookings"] if a["bookings"] else None


def report():
    print("=" * 72)
    print(f"PART 7 — MECHANISM COMPARISON (registered {REGISTERED})")
    print("=" * 72)

    print("\n[1] PRIOR, by mechanism")
    for k, p in PRIOR.items():
        c = f"${p['spend']/p['bookings']:.2f}/booking" if p["bookings"] else "no conversions"
        print(f"    {k:<9} ${p['spend']:7.2f} | {p['bookings']} bookings | {c}")
    hi = poisson_hi(0, PRIOR["form"]["spend"])
    print(f"    >> form best case ${1/hi:.2f}/booking; worst case it does not convert")

    print("\n[2] CURRENT STATE")
    print(f"    {'arm':<12} {'$/day':>6} {'spent':>8} {'events':>7} {'book':>5} {'cost/book':>10}")
    for k, a in ARMS.items():
        c = cpb(a)
        print(f"    {k:<12} {a['daily']:>6.2f} {a['spend']:>8.2f} {a['events']:>7} "
              f"{a['bookings']:>5} {('$'+format(c,'.2f')) if c else 'n/a':>10}")

    rate = PRIOR["messages"]["spend"] / PRIOR["messages"]["bookings"]

    print("\n[3] IS ARM B READY TO JUDGE?")
    b = ARMS["B_form"]
    if b["spend"] < MIN_SPEND_TO_JUDGE_B:
        exp = b["spend"] / rate
        print(f"    NO. ${b['spend']:.2f} of ${MIN_SPEND_TO_JUDGE_B:.2f} minimum.")
        print(f"    Expected {exp:.2f} bookings if equally good; "
              f"P(zero) = {np.exp(-exp):.1%}. Its zero means little yet.")
        print(f"    {(MIN_SPEND_TO_JUDGE_B-b['spend'])/b['daily']:.0f} more days to threshold.")
    else:
        print(f"    YES. ${b['spend']:.2f} spent.")

    print("\n[4] PROJECTION TO DAY 14")
    for k, a in ARMS.items():
        tot = a["daily"] * DAYS
        exp = tot / rate
        print(f"    {k:<12} ${tot:6.2f} | {exp:5.2f} expected | P(0) = {np.exp(-exp):.1%}")

    print("\n[5] WHAT THIS CAN AND CANNOT SETTLE")
    print("    CAN:    whether the message arm sustains ~$37/booking at 4x budget.")
    print("    CANNOT: whether forms are worse. Budget asymmetry and learning-phase")
    print("            behaviour at $5/day are inseparable from the mechanism.")
    print("    A loss for Arm B licenses 'the form bundle at $5/day did not")
    print("    convert', not 'forms do not work'.")


def evaluate(arm_a_spend, arm_a_bookings, arm_b_spend, arm_b_bookings):
    print("\n" + "=" * 72); print("RESULT"); print("=" * 72)
    for name, s, n in [("A_messages", arm_a_spend, arm_a_bookings),
                       ("B_form", arm_b_spend, arm_b_bookings)]:
        print(f"    {name:<12} ${s:7.2f} | {n} bookings | "
              f"{f'${s/n:.2f}' if n else 'no conversions'}")
    if arm_b_spend < MIN_SPEND_TO_JUDGE_B and arm_b_bookings == 0:
        print("\n    ARM B UNDERPOWERED — minimum not reached. Inconclusive, not a loss.")
    elif arm_a_bookings and arm_b_bookings:
        wa, wb = arm_a_spend / arm_a_bookings, arm_b_spend / arm_b_bookings
        print(f"\n    Winner: {'A_messages' if wa < wb else 'B_form'}")
    elif arm_a_bookings:
        print("\n    Arm B cleared its minimum and did not convert. Retire forms.")


if __name__ == "__main__":
    report()
    print("\n" + "=" * 72)
    print("FILL IN AFTER DAY 14")
    print("=" * 72)
    print("  evaluate(arm_a_spend=?, arm_a_bookings=?, arm_b_spend=?, arm_b_bookings=?)")

"""
OUTCOME: STOPPED EARLY, 2026-08-24.
Arm B was killed at $50.76 of its $112 pre-registered minimum, one day into
a 14-day window. The operator judged the form mechanism not worth further
spend given $101.81 of lifetime form spend across two campaigns with zero
bookings.

This is a business decision, not a test result. Arm B never reached the
sample size at which its zero becomes informative — at $50.76 an equally
good arm shows zero 25.8% of the time. The licensed claim is "the form
mechanism was abandoned before it could be evaluated", not "forms lost".

The pre-registered rule was violated by the person who wrote it. That is
recorded here rather than quietly dropped.
"""

"""
PROTOCOL DEVIATION, 2026-08-25. A third message variant (finished-car
video + one named slot) was sent ad hoc to leads in both arms after it
produced two revivals in 20 minutes on threads dead for 6+ weeks (L100,
Eduardo/L082). The A/B assignment is therefore contaminated. Recorded
here rather than dropped. The arms can no longer be cleanly compared;
the video variant should be tested on its own against a held-out set.
"""
