# Inland Auto Detailing — Growth, Ad Performance & Statistical Analytics

A two-part analytics project built on real operational data from **Inland Auto Detailing**, a mobile detailing business I own and operate across the Inland Empire and San Diego, CA. I'm the sole owner, the sole analyst, and the person who has to act on whatever the data says — every number in this repo has real money and real scheduling decisions behind it.

**Part 1 (`analysis.py`, `dashboard.html`)** answers three operational questions with data instead of guesswork: which acquisition channels are actually working, what current demand looks like by week/city/service tier, and whether the business can realistically run two markets at once.

**Part 2 (`ad_campaign_statistical_analysis.ipynb`)** goes further: it applies permutation testing and resampling inference — the techniques from UCSD DSC 10 and the broader HDSI lower-division sequence — to answer a harder question I ran into for real: when a spreadsheet shows one audience segment costing less per result than another, is that a real effect, or does it just look that way in a modest sample? The notebook tests it properly instead of eyeballing it, and the conclusion changed a live ad campaign I'm running as I write this.

## Why this exists

The business runs paid Meta ad campaigns and logs every job (date, city, service, acquisition channel, price) in a shared tracker. That data existed, but nobody had turned it into anything actionable — no channel-level ROAS, no demand pattern, no statistically grounded read on which audiences were actually worth targeting. This project does that, using the actual dataset, not a sanitized substitute.

## What's in here

```
inland-analytics/
├── data/
│   ├── job_log.csv                    # 35 logged jobs, cleaned/transcribed from the source tracker
│   ├── ad_spend.csv                   # 18 Meta ad campaigns, lifetime spend/impressions/results
│   ├── meta_ads_detailed_report.xlsx  # raw Meta export: 614 day/age/gender/campaign rows, Jan-Aug 2026
│   ├── messaging_only_raw.csv         # filtered to Result Type = "Messaging conversations started" (117 rows)
│   ├── messages_by_campaign.csv       # aggregated cost-per-message by campaign
│   ├── messages_by_demo.csv           # aggregated cost-per-message by age x gender
│   └── job_log_with_gender.csv        # 35 logged jobs with gender tagged, for Part 2 Section 6
├── analysis.py                         # Part 1: pandas script, cleans data, computes every metric
├── metrics.json                        # output of analysis.py — source of truth for the dashboard
├── dashboard.html                      # Part 1: self-contained interactive dashboard (Chart.js)
├── ads_analyzer.py                     # messages-per-1000-impressions analyzer + simple forward estimator
├── ad_campaign_statistical_analysis.ipynb  # Part 2: permutation tests, bootstrap CIs, full writeup
├── meta_ads_findings_report.docx       # narrative findings report (business audience)
├── ceramic_coating_campaign_tracker.xlsx   # live tracker for the campaign this analysis informed
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
```

To refresh with new jobs: update `data/job_log.csv` (and `data/ad_spend.csv` if ad spend changed), re-run `analysis.py`, then copy the new `metrics.json` contents into the `METRICS` constant near the bottom of `dashboard.html`.

## Methodology notes

- **Revenue basis**: the headline numbers use *priced, detail-service jobs only* (33 of 35 logged rows). Two rows are non-detail side jobs (a vinyl fencing job, a decor change). This 33-job figure independently matches the source tracker's own "33 jobs" label, which is a useful sanity check that the transcription and cleaning logic are correct.
- **Data quality finding**: the source sheet's own TOTALS row ($5,561) doesn't fully reconcile with the sum of its own `Total` column on a clean basis ($5,591) — most likely a `SUM()` range in the sheet that doesn't cover every row. `analysis.py` recomputes from raw rows rather than trusting the sheet's manual total.
- **ROAS**: Meta Ads is the only channel with real spend data (Meta Ads Manager lifetime export, 18 campaigns/ads). ROAS = revenue attributed to the "Meta Ads" channel in the job log ÷ total Meta ad spend. This undercounts true ROAS somewhat, since a few jobs logged under "Facebook" or "Instagram" almost certainly originated from the same ad account but weren't tagged consistently — a channel-tagging cleanup is a natural next step.
- **Two-location capacity model**: built off the actual combined job pace during the tracked period (7/18–8/9), not an assumption. Moreno Valley solo capacity is modeled at 70–100% of that current combined pace (a full-time operator should be able to hold or exceed it). San Diego is modeled conservatively at 1–3 jobs/week given zero existing customer base, zero reviews, and one working day available.

## Key findings

- **Meta Ads is the highest-ROI channel by both volume and ROAS**: 18 of 33 jobs, $3,135 in revenue, against $673.49 in lifetime ad spend — a **4.65x ROAS** and a **$37.42 blended cost per job**.
- **Door-to-door (D2D) is the second-largest channel** by job count but the lowest average ticket ($124.60 vs. $174.17 for Meta Ads) — worth knowing when comparing "free" channels to paid ones.
- **Saturday is the highest-revenue day**, consistent with weekend vehicle-owner availability — useful for scheduling and ad dayparting.
- **Moreno Valley is the single largest city by revenue**, reinforcing it as the right home base for the full-time operator.
- **Current combined throughput (~8.5 jobs/week) sets a defensible ceiling for what one full-time operator (Moreno Valley) can sustain solo**, and a realistic floor for what a one-day-a-week pilot market (San Diego) can produce starting from zero.

## Part 2: Statistical Findings

The full writeup, code, and plots are in `ad_campaign_statistical_analysis.ipynb`. Summary:

- Filtered a 614-row raw Meta export down to the 117 rows that actually represent messaging-objective results (159 total conversations, $312.13 spend) — an earlier, unfiltered version of this analysis had ranked two campaigns as top performers that turned out to be optimized for Instagram Profile Visits and Post Engagements, not messages. **Getting the label right mattered more than any downstream model choice.**
- Female audiences showed a $1.50/message rate vs. $2.36 for male — a **permutation test (10,000 resamples) puts this at p ≈ 0.0005**, i.e., a gap this large essentially never appears when the gender labels are shuffled at random.
- Age 55+ showed $1.53/message vs. $2.35 for under-55 — **p ≈ 0.0015** by the same method.
- Both results directly informed a live campaign launched August 20, 2026, targeting women 45+ within a 10-15 mile service radius. Its real performance is being logged in `ceramic_coating_campaign_tracker.xlsx` as a genuine forward test of the notebook's conclusion — not just a backtest.
- **A message isn't revenue — a booking is.** Section 6 tests a sharper question directly: does gender actually predict *booking*, not just messaging? Using real gender-tagged job data (`data/job_log_with_gender.csv`), the booking gender split (10 male / 8 female) was compared against the messaging gender split via 10,000 simulations under the null hypothesis of equal conversion rates. **Result: p ≈ 1.0 — no evidence the conversion rate differs by gender.** The cheaper-per-message finding for women (Section 4) does not carry through into who actually becomes a paying customer. This is the project's most important finding for how the account is actually run going forward: it stopped a plausible-sounding but unsupported assumption from turning into a real campaign decision, and reframed the live test around age instead.

## Possible next steps

- Tag ad campaigns with UTM parameters or campaign IDs that map directly to job-log entries, so ROAS can be computed per-campaign instead of per-channel.
- Once San Diego jobs start logging, extend `analysis.py` to break out both markets side by side and track the pilot against the model in this dashboard.
- Add a lightweight form (Google Form → Sheet) so job logging stays consistent going forward, closing the "no date logged" gaps in the early rows.
- Extend the permutation-testing framework in Part 2 to a proper randomized experiment: instead of testing whether an *observed* demographic split is real, run two ad sets with genuinely randomized audience assignment and test the difference directly — the stronger causal design the current observational approach can't fully deliver (see Limitations in the notebook).
- Once the ceramic coating campaign has enough real data, add its results as a third data point in the notebook and re-run the permutation test on the combined dataset to see if the effect size holds, grows, or shrinks with a genuine out-of-sample test.

## About me

I'm Isaac Castaneda, a UCSD student intending to major in Data Science through HDSI. I built and operate Inland Auto Detailing myself; this repo is the actual analytics stack I use to run it, not a class exercise built after the fact on a public dataset. Part 1 was built with pandas fundamentals; Part 2 applies resampling-based statistical inference to a real, live decision I had to make about ad targeting. I'm interested in research opportunities that let me keep applying rigorous methods to real, messy, self-collected data.
