import numpy as np
from scipy import stats

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
