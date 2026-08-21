"""
Meta Ads Analyzer + Predictor
================================
Two honest tools built from 16 real past campaigns (big camp and the
never-really-ran "Copy" campaign excluded - see meta_ads_report_v2.xlsx
for why):

1. ANALYZER - ranks campaigns by messages generated per 1,000 impressions
   (a fair apples-to-apples efficiency metric regardless of budget size),
   and checks which raw metrics (CPM, CTR, spend) actually correlate with
   that efficiency.

2. PREDICTOR - given a planned spend and an assumed CPM/conversion rate
   (pulled from one of your real past campaigns), estimates how many
   messages a similar new campaign might generate. This is a planning
   heuristic grounded in your own data, NOT a validated statistical
   model - 16 data points is nowhere near enough to trust a regression's
   confidence interval. Treat the number as a ballpark, not a promise.

Run:
    python3 ads_analyzer.py
"""
import numpy as np
import pandas as pd

DATA_PATH = "data/meta_ads_campaigns.csv"


def load():
    df = pd.read_csv(DATA_PATH)
    df["messages_per_1k_impr"] = df["messages"] / df["impressions"] * 1000
    df["cost_per_message"] = df.apply(
        lambda r: r["spend"] / r["messages"] if r["messages"] > 0 else np.nan, axis=1
    )
    return df


def analyzer(df):
    print("=" * 70)
    print("ANALYZER: ranked by messages per 1,000 impressions")
    print("=" * 70)
    ranked = df.sort_values("messages_per_1k_impr", ascending=False)
    for _, r in ranked.iterrows():
        cpm_str = f"${r['cpm']:.2f}"
        print(f"{r['campaign']:<32} {r['messages_per_1k_impr']:6.2f} msgs/1k impr   "
              f"CPM {cpm_str:<8} CTR {r['link_ctr']*100:4.2f}%   spend ${r['spend']:.2f}")

    print()
    print("Correlation with messages_per_1k_impr (n=%d, small sample - read directionally, not precisely):" % len(df))
    corr_cols = ["cpm", "link_ctr", "spend"]
    corrs = df[corr_cols + ["messages_per_1k_impr"]].corr()["messages_per_1k_impr"].drop("messages_per_1k_impr")
    for col, val in corrs.sort_values(key=abs, ascending=False).items():
        direction = "higher metric -> MORE messages/1k" if val > 0 else "higher metric -> FEWER messages/1k"
        print(f"  {col:<10} r = {val:+.2f}   ({direction})")

    print()
    top2 = ranked.head(2)
    rest = ranked.iloc[2:]
    cpm_corr = df[["cpm", "messages_per_1k_impr"]].corr().iloc[0, 1]
    print("Headline finding:")
    print(f"  Top 2 campaigns average {top2['messages_per_1k_impr'].mean():.1f} messages/1k impressions.")
    print(f"  Everything else averages {rest['messages_per_1k_impr'].mean():.1f} messages/1k impressions.")
    print(f"  That's a {top2['messages_per_1k_impr'].mean() / max(rest['messages_per_1k_impr'].mean(), 0.01):.1f}x gap.")
    if cpm_corr < -0.2:
        print(f"  The top performers also have low CPMs relative to the dataset (r={cpm_corr:+.2f}) -")
        print(f"  consistent with Meta's auction rewarding ads people actually engage with.")
    elif cpm_corr > 0.2:
        print(f"  CPM is NOT the driver here (r={cpm_corr:+.2f}, higher CPM associated with MORE messages/1k,")
        print(f"  the opposite of the cheap-reach story). With only {len(df)} campaigns this could easily be")
        print(f"  noise or reverse causation (Meta may have raised CPM because these were performing well) -")
        print(f"  don't repeat this as a rule without a larger sample.")
    else:
        print(f"  CPM shows no meaningful relationship to message rate here (r={cpm_corr:+.2f}).")


def predictor(df, planned_spend, like_campaign):
    print()
    print("=" * 70)
    print("PREDICTOR: estimate for a new campaign")
    print("=" * 70)
    row = df[df["campaign"] == like_campaign].iloc[0]
    rate = row["messages_per_1k_impr"]
    cpm = row["cpm"]
    est_impressions = planned_spend / cpm * 1000
    est_messages = est_impressions * rate / 1000
    est_cost_per_message = planned_spend / est_messages if est_messages > 0 else float("nan")

    print(f"Modeling this campaign after: '{like_campaign}'")
    print(f"  (assumes similar CPM ~${cpm:.2f} and similar creative resonance: {rate:.1f} msgs/1k impressions)")
    print(f"Planned spend: ${planned_spend:.2f}")
    print(f"  -> Estimated impressions: {est_impressions:,.0f}")
    print(f"  -> Estimated messages:    {est_messages:.1f}")
    print(f"  -> Estimated cost/message: ${est_cost_per_message:.2f}")
    print()
    print("Caveat: this is a straight-line extrapolation of one past campaign's rate.")
    print("It assumes the new creative performs as well as your best historical one -")
    print("that's an optimistic assumption, not a guarantee. Use it as a target to beat,")
    print("not a forecast to bank on. Re-run this with real numbers after 2-3 days live")
    print("to see if the new campaign is tracking toward or away from this estimate.")


if __name__ == "__main__":
    df = load()
    analyzer(df)
    # Example: planning a $75 ceramic-coating campaign, modeled on the best CONFIRMED
    # messages-objective creative (Turning a side / Algae v2 were excluded from this
    # dataset - they were Profile Visits / Post Engagements campaigns, not Messages)
    predictor(df, planned_spend=75.0, like_campaign="New Engagement Campaign #1")
