"""Fail if the README no longer states the computed figures. Run before push."""
import pandas as pd, re, sys
d = pd.read_csv("data/job_log.csv")
d["total"] = d.job_value.fillna(0) + d.tip.fillna(0)
det = d[d.is_detail_job == 1]
spend = pd.read_csv("data/ad_spend.csv").amount_spent.sum()
attr = det[(det.channel == "Meta Ads") & (det.ad_attributed == 1)]
L = pd.read_csv("data/leads_anonymized.csv")
rd = open("README.md").read()

checks = [
    (f"{len(det)} ", "detail job count"),
    (f"{det.total.sum():,.0f}", "gross revenue"),
    (f"{det.total.mean():.2f}", "average ticket"),
    (f"{spend:,.2f}", "lifetime spend"),
    (f"{attr.total.sum()/spend:.2f}x", "ad-attributed ROAS"),
    (f"{len(L)}", "lead count"),
]
bad = [(v, lbl) for v, lbl in checks if v.strip() not in rd]
for v, lbl in bad:
    print(f"DRIFT: README does not state {lbl} = {v}")
if not bad:
    print("README matches the data.")
sys.exit(1 if bad else 0)
