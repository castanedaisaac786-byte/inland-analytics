# Inland Auto Detailing — Growth, Ad Performance & Statistical Analytics

A five-part analytics project built on real operational data from **Inland Auto Detailing**, a mobile detailing business I own and operate across the Inland Empire and San Diego, CA. I'm the sole owner, the sole analyst, and the person who has to act on whatever the data says — every number in this repo has real money and real scheduling decisions behind it.

**Part 1** (`analysis.py`, `dashboard.html`) — operational dashboard. Channel ROAS, weekly demand, city and service-tier mix, and the data-quality errors that had to be fixed before any of it could be trusted.

**Part 2** (`ad_campaign_statistical_analysis.ipynb`) — permutation testing and resampling inference on ad targeting data. Found a real cost-per-message gap by gender, then tested whether it predicted *bookings* and found that it didn't.

**Part 3** (`part3_maintenance_conversion/`) — retention funnel and channel comparison. Returns an honest non-result (p = 1.000) plus a power calculation showing exactly how much more data it would take.

**Part 4** (`part4_placement_analysis.py`) — permutation tests on ad *placement* efficiency across 456 rows of Meta delivery data. Tested a hypothesis I had already acted on, and found I was half wrong.

**Part 5** (`part5_campaign_experiment.py`) — a live two-arm experiment testing whether the acquisition *mechanism* drives bookings, with a pre-registered decision rule and an explicit confound audit.

---

## The through-line

Each part exists because the previous one hit a wall. That chain is the actual content of this repo:

| Step | Finding | Limitation that motivated the next step |
|---|---|---|
| **P2 §4** | Cost per message differs by gender (p≈0.0005) and age (p≈0.0015) | These are *cost* findings. Cheap to reach ≠ likely to buy. |
| **P2 §6** | Gender does **not** predict booking (p≈1.0) | Killed a campaign decision. But left open *why* messages weren't converting. |
| **Aug 2026** | A live campaign: 28 messages in 48 hours, **0 bookings** | Hypothesis: cheap placements (Reels, Stories) generate junk taps. |
| **P4** | Reels is the *cheapest* placement and 58% of volume. Stories is the expensive one (p=0.0004). | Half the hypothesis was wrong. And placement data has **no bookings** — so it could only rank by cost, exactly the P2 §4 limitation again. |
| **P5** | Targeting widened → messages went **up**, bookings stayed at **0** | Targeting is not the binding constraint. Test the mechanism instead. |

**Three times now, a cost-side improvement has failed to move revenue.** That's consistent enough to treat as an operating rule rather than a surprise: optimize the conversion step, not the acquisition step.

---

## Why this exists

The business runs paid Meta ad campaigns and logs every job (date, city, service, acquisition channel, price) in a shared tracker. That data existed, but nobody had turned it into anything actionable — no channel-level ROAS, no demand pattern, no statistically grounded read on which audiences were actually worth targeting. This project does that, using the actual dataset, not a sanitized substitute.

## What's in here

```
inland-analytics/
├── data/
│   ├── job_log.csv                    # logged jobs, cleaned/transcribed from the source tracker
│   ├── ad_spend.csv                   # Meta ad campaigns, lifetime spend/impressions/results
│   ├── meta_ads_detailed_report.xlsx  # raw Meta export: 614 day/age/gender/campaign rows
│   ├── placement_report.xlsx          # Meta placement export: 494 day x ad x placement rows
│   ├── messaging_only_raw.csv         # filtered to Result Type = "Messaging conversations started"
│   ├── messages_by_campaign.csv       # aggregated cost-per-message by campaign
│   ├── messages_by_demo.csv           # aggregated cost-per-message by age x gender
│   └── job_log_with_gender.csv        # jobs with gender tagged, for Part 2 Section 6
├── analysis.py                             # Part 1: cleans data, computes every metric
├── metrics.json                            # output of analysis.py — source of truth for the dashboard
├── dashboard.html                          # Part 1: self-contained interactive dashboard (Chart.js)
├── ads_analyzer.py                         # messages-per-1000-impressions analyzer
├── ad_campaign_statistical_analysis.ipynb  # Part 2: permutation tests, bootstrap CIs, writeup
├── meta_ads_findings_report.docx           # narrative findings report (business audience)
├── ceramic_coating_campaign_tracker.xlsx   # live tracker for the campaign this analysis informed
├── part3_maintenance_conversion/           # Part 3: funnel, channel test, power calc
├── part4_placement_analysis.py             # Part 4: placement permutation tests
├── part5_campaign_experiment.py            # Part 5: live experiment design + decision rule
├── refresh.py                              # one-command update: reruns Parts 1 & 3, resyncs dashboard
└── README.md
```

## How to run it

```bash
pip install pandas numpy scipy matplotlib jupyter openpyxl

python3 analysis.py                  # Part 1 — regenerates metrics.json
open dashboard.html                  # everything embedded, no server required

jupyter notebook ad_campaign_statistical_analysis.ipynb   # Part 2

cd part3_maintenance_conversion/notebooks && python3 analysis.py   # Part 3

python3 part4_placement_analysis.py  # Part 4 — placement permutation tests
python3 part5_campaign_experiment.py # Part 5 — experiment design + thresholds
```

**To refresh with new jobs or ad spend:** update `data/job_log.csv` and/or `data/ad_spend.csv`, then run `python3 refresh.py`. Written claims in this README don't update themselves — check them against `refresh.py` output after any real data change.

---

## Methodology notes

- **Revenue basis**: headline numbers use *priced, vehicle-detail-service jobs only*. Four rows are non-detail side jobs (vinyl fencing, a decor change, garage organization, party planning), and four more are pressure-washing jobs — reclassified as non-detail since exterior/patio pressure washing isn't a vehicle-detailing service, even though the source tracker counted it as one. Full reasoning is in the live Data Quality Note in `dashboard.html`, generated directly by `analysis.py` so it can't go stale independently of the data.

- **⚠️ Revenue is GROSS, not net of labor.** Nearly every job is worked with a second person on a revenue split, and that cost is **not currently modeled anywhere in this repo**. Every "ROI" figure below is therefore a revenue figure, not a profit figure. Adding a `labor_cost` column and recomputing contribution margin per channel is the single highest-priority fix outstanding — it may reverse the channel ranking, since the paid channel carries acquisition cost that the free channel does not.

- **Data quality findings**: two rows had stale `total` values that didn't reconcile with `job_value + tip` (a manual entry error — the total wasn't recalculated after a tip was added). `analysis.py` recomputes from raw rows rather than trusting any manually-entered total, and the fallback logic was hardened so a future blank `total` cell can't silently drop a tip again.

- **Zero-result rows are included, not dropped.** In Part 4, 375 of 494 placement rows recorded spend with no messaging results. They're counted as zero, not filtered out — dropping them would overstate efficiency for placements that burned spend for nothing. This is the same filtering error that inflated a campaign gap to 18.6x in Part 2.

- **ROAS**: Meta Ads is the only channel with real spend data. ROAS = revenue attributed to the "Meta Ads" channel ÷ total Meta spend. This undercounts somewhat, since a few jobs logged under "Facebook" or "Instagram" almost certainly came from the same ad account.

---

## Key findings — Part 1

- **Meta Ads leads by volume and gross ROAS**: 19 jobs, $3,525 revenue against $673.49 lifetime spend — **5.23x ROAS**, $35.45 blended cost per job. *(Gross. See the labor-cost caveat above.)*
- **D2D is second by job count but lowest average ticket** ($118 vs $186 for Meta Ads) — worth knowing when comparing "free" channels to paid ones.
- **Saturday is the highest-revenue day** — useful for scheduling and ad dayparting.
- **Moreno Valley is the largest city by revenue**, reinforcing it as the right home base.

## Part 2: Statistical Findings

- Filtered a 614-row raw Meta export to the 117 rows representing messaging-objective results. An earlier unfiltered version had ranked two campaigns as top performers that were actually optimized for Instagram Profile Visits and Post Engagements. **Getting the label right mattered more than any downstream model choice.**
- Female audiences: **$1.50/message vs $2.36 for male** — permutation test, 10,000 resamples, **p ≈ 0.0005**.
- Age 55+: **$1.53/message vs $2.35** for under-55 — **p ≈ 0.0015**.
- **§6 — A message isn't revenue, a booking is.** Tested whether gender predicts *booking* using gender-tagged job data. 10,000 simulations under a null of equal conversion. **Result: p ≈ 1.0.** The cheaper-per-message finding does not carry through into who becomes a paying customer. This stopped a plausible-sounding assumption from becoming a real campaign decision.
- `ads_analyzer.py` ranks campaigns by messages per 1,000 impressions. Top performer: **New Engagement Campaign #1 at 7.92 msgs/1k**, a **3.2x** gap. CPM correlates *positively* with message rate (r = +0.52), the opposite of a "cheap reach wins" story. An earlier version had two miscategorized campaigns inflating that gap to 18.6x — removing them changed the finding's **direction**, not just its size.

## Part 3: Maintenance Conversion

- **The leak isn't rejection, it's silence.** Of 24 maintenance candidates pitched, **46% never responded at all.** The fix is a follow-up cadence that forces a yes/no, not a better pitch.
- **D2D converts to recurring maintenance at 29% (n=7) vs Meta Ads' 20% (n=15)** — inverted from what higher ticket size would predict.
- **But that gap is not distinguishable from chance.** Permutation test, 10,000 resamples: **p = 1.000**. With 7 D2D candidates, the observed 8.6-point gap is the *smallest possible non-zero outcome* the data could produce.
- **Power calculation**: detecting this gap at 95% confidence / 80% power needs **~389 pitched candidates per channel** — 56x current D2D volume. Recalculated on every run.

## Part 4: Placement Efficiency

Tested a hypothesis I had **already acted on**: that cheap placements (Reels, Stories) were generating accidental-tap messages that never convert.

Window Jun 15 – Aug 21, 2026 · $752.68 spend · 186 messages · 45,158 impressions · 456 rows with spend.

| Comparison | Cost per message | Gap | p |
|---|---|---|---|
| Feed vs **Reels** | $4.47 vs **$3.46** | +$1.01 | **0.205** |
| Feed vs Stories | $4.47 vs $8.03 | −$3.56 | 0.058 |
| **Reels vs Stories** | **$3.46** vs $8.03 | −$4.57 | **0.0004** |

- **Reels is the cheapest placement and carries 58% of all message volume.** Feed is nominally more expensive, but at p = 0.205 that gap isn't distinguishable from chance.
- **Stories is the genuinely expensive placement** — $8.03/msg against Reels' $3.46, p = 0.0004.
- **I had excluded both.** Cutting Stories was supported. Cutting Reels removed the highest-volume placement in the account on an untested assumption, and was reversed.
- **What this cannot answer**: the placement export contains no bookings. So it ranks placements by *cost*, not by lead quality — the exact limitation as Part 2 §4. A cheap placement could be efficient or could be junk, and this dataset cannot tell them apart.

## Part 5: Campaign Mechanism Experiment

After targeting was widened, message volume rose and bookings stayed at zero. **31 messages, $51.00 spend, 0 bookings** ($1.65/msg).

- **P(0 bookings | benchmark conversion rate of 19.2%) = 0.133%.** The current campaign converting worse than the reference campaign is now well-supported, not a hunch.
- **95% upper bound on true conversion rate: 9.2%.**
- **Break-even to match the $26.09/booking benchmark: 6.3%** — 2 bookings out of 31. Still viable, but the margin is closing.
- **What this already proves**: targeting widened, messages went up, revenue didn't move. Targeting is not the binding constraint.

Two campaigns now run simultaneously to test whether the **acquisition mechanism** — instant form plus 15-minute callback, versus Messenger conversation — is what drives bookings.

`part5_campaign_experiment.py` includes an explicit **confound audit**: four variables differ between arms (objective, age range, Stories placement, response speed). The script states plainly that this is a test of *bundle A vs bundle B*, not "forms vs messages," and that a loss for the form arm is uninterpretable because it carries the known-bad Stories placement. The decision rule is **pre-registered**: 14 days or $100 per arm, judged on cost per booking only, act on the winner even without significance.

---

## Current Status

*Last verified: August 22, 2026*

- **29 billable detail jobs**, **$4,721 gross revenue**, **$162.79 average ticket** *(gross — labor cost not yet modeled)*
- **Meta Ads**: 19 jobs, $3,525 revenue, 5.23x gross ROAS, $35.45 blended cost per job
- **D2D**: 8 jobs, $946 revenue, $118 average ticket, near-zero acquisition cost
- **Maintenance conversion**: 21% positive, 8% confirmed; D2D directionally ahead (29% vs 20%) but not provable (p = 1.000; needs ~389 pitched per channel)
- **Placement**: Reels cheapest at $3.46/msg and 58% of volume; Stories worst at $8.03/msg (p = 0.0004 vs Reels)
- **Live experiment**: two arms running, decision rule pre-registered, results pending

Every number above is regenerated by `python3 refresh.py`. Check it against that output before trusting anything written here.

## Known gaps

Listed because they're the honest limits on everything above:

1. **Labor cost is unmodeled.** Every revenue and ROAS figure is gross. Adding it may reverse the channel ranking.
2. **The reference campaign's 5 bookings are recalled, not logged.** The $26.09/booking benchmark — and every threshold derived from it in Part 5 — rests on an unverified number.
3. **No booking attribution by campaign or placement.** `campaign_arm` and `placement` columns on `job_log.csv` would make Parts 4 and 5 answerable rather than merely well-designed.
4. **Ad delivery was never randomized.** Meta's optimizer chose who saw what, so every demographic result is observational. Permutation testing the labels of a non-randomly-assigned sample tests whether a split is unusual given the marginals — not whether the trait causes the outcome.

## Possible next steps

- Add `labor_cost`, `campaign_arm`, and `placement` to `job_log.csv` and recompute contribution margin per channel. **Highest priority — it gates gaps 1–3 above.**
- Rerun Part 4 on bookings-per-placement instead of cost-per-message once ~20 bookings are tagged.
- Extend the permutation framework to a genuinely randomized experiment: two ad sets with random audience assignment, testing the difference directly — the causal design the current observational approach can't deliver.
- Once San Diego jobs start logging, break out both markets side by side.
- Re-run Parts 2 and 3 as real out-of-sample data accumulates, to see whether effect sizes hold, grow, or shrink.

## About me

I'm Isaac Castaneda, a UCSD student majoring in Data Science through HDSI. I built and operate Inland Auto Detailing myself; this repo is the actual analytics stack I use to run it, not a class exercise built after the fact on a public dataset. I'm interested in research opportunities that let me keep applying rigorous methods to real, messy, self-collected data.
