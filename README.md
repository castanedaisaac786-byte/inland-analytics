# Inland Auto Detailing — Growth, Ad Performance & Statistical Analytics

A three-part analytics project built on real operational data from **Inland Auto Detailing**, a mobile detailing business I own and operate across the Inland Empire and San Diego, CA. I'm the sole owner, the sole analyst, and the person who has to act on whatever the data says — every number in this repo has real money and real scheduling decisions behind it.

**Part 1** (`analysis.py`, `dashboard.html`) answers operational questions with data instead of guesswork: which acquisition channels are actually working, what current demand looks like by week/city/service tier, and where the business's own data had errors that needed fixing before any of that could be trusted.

**Part 2** (`ad_campaign_statistical_analysis.ipynb`) goes further: it applies permutation testing and resampling inference — techniques ahead of the intro data science sequence — to answer a harder question I ran into for real: when a spreadsheet shows one audience segment costing less per result than another, is that a real effect, or does it just look that way in a modest sample? The notebook tests it properly instead of eyeballing it, and the conclusion changed a live ad campaign I'm running as I write this.

**Part 3** (`part3_maintenance_conversion/`) goes back to the first problem I actually had, before ad ROI was even the question: retention. It applies the same permutation-testing rigor from Part 2 to a smaller, harder dataset — and returns an honest non-result (p = 1.000) plus a real power calculation showing exactly how much more data it would take to prove what looks like a pattern. Knowing when you *can't* claim something yet is the same skill as knowing when you can.

## Why this exists

The business runs paid Meta ad campaigns and logs every job (date, city, service, acquisition channel, price) in a shared tracker. That data existed, but nobody had turned it into anything actionable — no channel-level ROAS, no demand pattern, no statistically grounded read on which audiences were actually worth targeting. This project does that, using the actual dataset, not a sanitized substitute.

## What's in here

```
inland-analytics/
├── data/
│   ├── job_log.csv                    # logged jobs, cleaned/transcribed from the source tracker
│   ├── ad_spend.csv                   # Meta ad campaigns, lifetime spend/impressions/results
│   ├── meta_ads_detailed_report.xlsx  # raw Meta export: 614 day/age/gender/campaign rows, Jan-Aug 2026
│   ├── messaging_only_raw.csv         # filtered to Result Type = "Messaging conversations started" (117 rows)
│   ├── messages_by_campaign.csv       # aggregated cost-per-message by campaign
│   ├── messages_by_demo.csv           # aggregated cost-per-message by age x gender
│   └── job_log_with_gender.csv        # jobs with gender tagged, for Part 2 Section 6
├── analysis.py                         # Part 1: pandas script, cleans data, computes every metric
├── metrics.json                        # output of analysis.py — source of truth for the dashboard
├── dashboard.html                      # Part 1: self-contained interactive dashboard (Chart.js)
├── ads_analyzer.py                     # messages-per-1000-impressions analyzer + simple forward estimator
├── ad_campaign_statistical_analysis.ipynb  # Part 2: permutation tests, bootstrap CIs, full writeup
├── meta_ads_findings_report.docx       # narrative findings report (business audience)
├── ceramic_coating_campaign_tracker.xlsx   # live tracker for the campaign this analysis informed
├── part3_maintenance_conversion/       # Part 3: funnel, channel comparison, permutation test, power calc
│   ├── data/
│   ├── notebooks/analysis.py
│   └── figures/
├── refresh.py                          # one-command update: reruns Parts 1 & 3, resyncs the dashboard
└── README.md
```

## How to run it

```bash
pip install pandas numpy matplotlib jupyter

# Part 1 — operational dashboard
python3 analysis.py         # regenerates metrics.json from the CSVs
open dashboard.html          # everything is embedded, no server required

# Part 2 — statistical analysis notebook
jupyter notebook ad_campaign_statistical_analysis.ipynb

# Part 3 — maintenance conversion analysis
cd part3_maintenance_conversion/notebooks && python3 analysis.py
```

**To refresh with new jobs or ad spend:** update `data/job_log.csv` and/or `data/ad_spend.csv`, then run `python3 refresh.py` from the repo root. It reruns Part 1, resyncs `dashboard.html` automatically, reruns Part 3, and prints exactly what changed. Written claims in this README (the specific dollar figures and percentages below) don't update themselves — check them against `refresh.py`'s printed output after any real data change and edit by hand if something moved.

## Methodology notes

- **Revenue basis**: the headline numbers use *priced, vehicle-detail-service jobs only*. Four rows are non-detail side jobs (vinyl fencing, a decor change, garage organization, party planning), and four more are pressure-washing jobs — reclassified as non-detail since exterior/patio pressure washing isn't a vehicle-detailing service, even though the source tracker originally counted it as one. This is a narrower, more deliberate definition of "detail" than the source sheet used. Full reasoning is in the live Data Quality Note in `dashboard.html`, which is generated directly by `analysis.py` so it can't go stale independently of the data.
- **Data quality findings**: two rows had stale `total` values that didn't reconcile with `job_value + tip` (a manual spreadsheet entry error — the total wasn't recalculated after a tip was added after the fact). `analysis.py` recomputes from raw rows rather than trusting any manually-entered total, and the fallback logic itself was hardened after this was found, so a future blank `total` cell can't silently drop a tip again.
- **ROAS**: Meta Ads is the only channel with real spend data (Meta Ads Manager lifetime export). ROAS = revenue attributed to the "Meta Ads" channel in the job log ÷ total Meta ad spend. This undercounts true ROAS somewhat, since a few jobs logged under "Facebook" or "Instagram" almost certainly originated from the same ad account but weren't tagged consistently — a channel-tagging cleanup is a natural next step.

## Key findings

- **Meta Ads is the highest-ROI channel by both volume and ROAS**: 19 jobs, $3,525 in revenue, against $673.49 in lifetime ad spend — a **5.23x ROAS** and a **$35.45 blended cost per job**.
- **Door-to-door (D2D) is the second-largest channel** by job count but the lowest average ticket ($118 vs. $186 for Meta Ads) — worth knowing when comparing "free" channels to paid ones.
- **Saturday is the highest-revenue day**, consistent with weekend vehicle-owner availability — useful for scheduling and ad dayparting.
- **Moreno Valley is the single largest city by revenue**, reinforcing it as the right home base.

## Part 2: Statistical Findings

The full writeup, code, and plots are in `ad_campaign_statistical_analysis.ipynb`. Summary:

- Filtered a 614-row raw Meta export down to the 117 rows that actually represent messaging-objective results (159 total conversations, $312.13 spend) — an earlier, unfiltered version of this analysis had ranked two campaigns as top performers that turned out to be optimized for Instagram Profile Visits and Post Engagements, not messages. **Getting the label right mattered more than any downstream model choice.**
- Female audiences showed a $1.50/message rate vs. $2.36 for male — a **permutation test (10,000 resamples) puts this at p ≈ 0.0005**, i.e., a gap this large essentially never appears when the gender labels are shuffled at random.
- Age 55+ showed $1.53/message vs. $2.35 for under-55 — **p ≈ 0.0015** by the same method.
- Both results directly informed a live campaign launched August 20, 2026, targeting women 45+ within a 10-15 mile service radius. Its real performance is being logged in `ceramic_coating_campaign_tracker.xlsx` as a genuine forward test of the notebook's conclusion — not just a backtest.
- **A message isn't revenue — a booking is.** Section 6 tests a sharper question directly: does gender actually predict *booking*, not just messaging? Using real gender-tagged job data (`data/job_log_with_gender.csv`), the booking gender split (10 male / 8 female) was compared against the messaging gender split via 10,000 simulations under the null hypothesis of equal conversion rates. **Result: p ≈ 1.0 — no evidence the conversion rate differs by gender.** The cheaper-per-message finding for women (Section 4) does not carry through into who actually becomes a paying customer. This is the project's most important finding for how the account is actually run going forward: it stopped a plausible-sounding but unsupported assumption from turning into a real campaign decision, and reframed the live test around age instead.
- A separate tool, `ads_analyzer.py`, ranks past campaigns by messages generated per 1,000 impressions (a fair efficiency metric regardless of budget size). The real top performer is **New Engagement Campaign #1 at 7.92 msgs/1k impressions**, a genuine **3.2x** gap over the rest of the dataset — and CPM correlates *positively* with message rate here (r=+0.52), the opposite of a "cheap reach wins" story. An earlier version of this analysis had two miscategorized campaigns inflating that gap to 18.6x; removing them changed the finding's direction, not just its size.

## Part 3: Maintenance Conversion Analysis

A third, earlier piece of the same work — before ad ROI was the question, the first problem was retention. Full code, data, and figures are in `part3_maintenance_conversion/`.

- **The leak isn't rejection, it's silence.** Of 24 maintenance candidates pitched, 46% never responded at all — not a "no," just nothing. That reframes the fix: the priority is a follow-up cadence that forces a real yes/no, not a better pitch script.
- **Acquisition channel predicts loyalty, inverted from what you'd expect.** D2D converts to recurring maintenance at 29% (n=7) vs. Meta Ads' 20% (n=15), despite Meta Ads customers paying more per job on average ($186 vs $118).
- **But that gap is not yet statistically distinguishable from chance.** A permutation test (10,000 resamples, same method as Part 2) returns **p = 1.000**. With only 7 D2D candidates pitched so far, the observed 8.6-point gap is actually the *smallest* possible non-zero outcome the data could produce — nearly every random relabeling produces a gap at least as large by chance alone.
- **A real power calculation, not a guess, on what it would take to prove this**: at current observed rates, detecting this gap at 95% confidence / 80% power would need **~389 pitched candidates per channel** — D2D would need **56x** its current sample. That's a real target to track as the maintenance program scales, not something achievable soon at current volume. The script recalculates this figure every run, so it's a live number that should shrink as real data accumulates.

Run it: `cd part3_maintenance_conversion/notebooks && python3 analysis.py`

## Current Status

*Last verified: August 21, 2026, via `python3 refresh.py`*

- **29 billable detail jobs**, **$4,721 total revenue**, **$162.79 average ticket**
- **Meta Ads**: 19 jobs, $3,525 revenue, **5.23x ROAS**, $35.45 blended cost per job — the highest-ROI channel by both volume and return
- **D2D**: 8 jobs, $946 revenue, $118 average ticket — lower per-job than Meta Ads but near-zero acquisition cost
- **Maintenance conversion**: 21% positive rate, 8% confirmed; D2D directionally outperforms Meta Ads (29% vs 20%) but this isn't statistically provable yet (p = 1.000; needs ~389 pitched per channel to confirm)
- **Ad efficiency**: New Engagement Campaign #1 is the real top performer at 7.92 msgs/1k impressions, a genuine 3.2x gap over the rest of the dataset

This is a snapshot, not a permanent conclusion — every number above is regenerated automatically by `python3 refresh.py`. Check it against that script's live output before trusting anything written here, since the underlying data changes every time a new job or campaign gets logged.

## Possible next steps

- Tag ad campaigns with UTM parameters or campaign IDs that map directly to job-log entries, so ROAS can be computed per-campaign instead of per-channel.
- Once San Diego jobs start logging, extend `analysis.py` to break out both markets side by side.
- Add a lightweight form (Google Form → Sheet) so job logging stays consistent going forward, closing the "no date logged" gaps in the early rows.
- Extend the permutation-testing framework to a proper randomized experiment: instead of testing whether an *observed* demographic split is real, run two ad sets with genuinely randomized audience assignment and test the difference directly — the stronger causal design the current observational approach can't fully deliver.
- Once the ceramic coating campaign and the maintenance program both have more real data, re-run the permutation tests in Parts 2 and 3 to see if the effect sizes hold, grow, or shrink with genuine out-of-sample evidence.

## About me

I'm Isaac Castaneda, a UCSD student intending to major in Data Science through HDSI. I built and operate Inland Auto Detailing myself; this repo is the actual analytics stack I use to run it, not a class exercise built after the fact on a public dataset. I'm interested in research opportunities that let me keep applying rigorous methods to real, messy, self-collected data.
