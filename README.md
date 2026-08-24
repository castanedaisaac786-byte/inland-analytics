# Inland Auto Detailing — Growth, Ad Performance & Statistical Analytics

A seven-part analytics project built on real operational data from **Inland Auto Detailing**, a mobile detailing business I own and operate across the Inland Empire and San Diego, CA. I'm the sole owner, the sole analyst, and the person who has to act on whatever the data says — every number in this repo has real money and real scheduling decisions behind it.

Every statistical claim below has been re-executed from source in a clean environment. Where a published figure failed to reproduce, the corrected value is here and the error is documented.

---


## Data Quality & Verification Audit

Every published figure in this repo was re-derived from raw source logs.
**Thirteen failed verification and were corrected. One of them was the
project's headline finding.**

This is a living log. New corrections are appended, never quietly patched.

| # | Figure | Published | Corrected | How it was found |
|---|---|---|---|---|
| 1 | **§4 gender effect** | $1.50 vs $2.36, **p = 0.0005** | $3.49 vs $3.95, **p = 0.4519** | `messaging_only_raw.csv` keeps only rows with ≥1 message, dropping 48% of messaging spend. **This is the exact rule Part 4 states** — applied to Part 2 for the first time |
| 2 | Meta ROAS | 5.23x | **3.20x** | Numerator included $1,010 of organic DMs mistagged as paid; denominator understated spend |
| 3 | Lifetime ad spend | $673.49 | **$786.08** | `ad_spend.csv` was stale. Rebuilt from the deduplicated export |
| 4 | §6 p-value | p ≈ 1.0 | **p = 0.822** | Notebook re-executed in a clean venv |
| 5 | Cost-per-booking benchmark | $26.09 | **$69.52** | Built on 5 *recalled* bookings; the log shows 2 |
| 6 | Part 5 benchmark denominator | 26 messages | **49 messages** | Numerator and denominator came from two different creatives |
| 7 | Part 5 live arm | $95.01 / 58 msgs | **$56.61 / 34** | The published figure reconciled to no campaign in any export |
| 8 | Part 3 "$840 tip discrepancy" | $840 | **$40** | A basis mismatch between detail-only and all-jobs revenue. The real tip error is one row |
| 9 | Tip-drop bug | "fixed" | **recurring** | A third instance appeared after the fix was documented |
| 10 | Part 4 reproducibility | "runs" | **crashed** | The committed placement file was a different export. Fixed |
| 11 | "Save 2007 Chevy" attribution | 4 bookings | **0 click-attributed** | That ad ID appears in none of 116 leads |
| 12 | "Patrick Ads" spend | $130.00 | **no such campaign** | A hand-typed round number published as a measured cost |
| 13 | Part 3 "the leak is silence" | 46% never responded (n=24) | **19.8% (n=116)** | The dominant failure mode is stalled mid-conversation (56%) |

### Why #1 is the most important entry

The gender result was the first row of the through-line, the basis for a live
campaign, and the figure quoted most often. It died when I applied a rule I
had already written down in Part 4 — *"dropping zero-result rows would
overstate efficiency"* — to the section where I had not yet applied it.

The age finding survived the same test ($2.90 vs $4.52, p = 0.0097).

**A verification process that never overturns your best result is not a
verification process.**

### Reproducibility

CI runs on every push: `pytest tests/` plus a full execution of Parts 1, 3, 4,
5, 6, 7 and the Section 4 re-analysis. The test suite encodes the bug classes
above as assertions — including one that fails if cost-per-event is ever
computed over only the units that produced an event.

## The through-line

Each part exists because the previous one hit a wall. That chain is the actual content of this repo.

| Step | Finding | Limitation that forced the next step |
|---|---|---|
| **P2 §4** | Cost per message differs by gender (p = 0.0005) and age (p = 0.0015) | These are *cost* findings. Cheap to reach ≠ likely to buy. |
| **P2 §6** | Gender does **not** predict booking (p = 0.822) | Killed a campaign decision. Left open *why* messages weren't converting. |
| **P3** | D2D retention beats Meta Ads by 8.6 pts — but p = 1.000 | Underpowered. Needs ~389 pitched per channel. |
| **Aug 2026** | A campaign produced 28 messages in 48 hours, **0 bookings** | Hypothesis: cheap placements were generating junk taps. |
| **P4** | Reels is the *cheapest* placement and 58% of volume. Stories is the expensive one (p = 0.0004). | Half the hypothesis was wrong — and placement data has no bookings, so it could only rank by cost. Same limitation as §4. |
| **P5** | Targeting widened → messages up, bookings still 0 | Targeting is not the binding constraint. |
| **P6** | Creative is the lever. **7.2x spread** in cost per booking across creatives. | The answer, and it required the one dataset the earlier parts lacked. |
| **P7** | Pre-registered scale-up test on the winning creative | First forward prediction in the project. |

**Four times, a cost-side improvement failed to move revenue.** That's now the operating rule: optimize the conversion step, not the acquisition step.

---

## What's in here

```
inland-analytics/
├── data/
│   ├── job_log.csv                    # creative_hook, platform_destination, ad_attributed
│   ├── ad_spend.csv                   # Meta campaigns, lifetime spend/impressions/results
│   ├── placement_report.xlsx          # 494 day x ad x placement rows
│   ├── meta_ads_detailed_report.xlsx  # 614 day/age/gender/campaign rows
│   ├── messaging_only_raw.csv         # filtered to messaging-objective results
│   └── job_log_with_gender.csv        # gender-tagged jobs, for Part 2 §6
├── analysis.py                             # P1: cleans data, computes every metric
├── metrics.json                            # output of analysis.py — dashboard source of truth
├── dashboard.html                          # P1: self-contained dashboard (Chart.js)
├── ad_campaign_statistical_analysis.ipynb  # P2: permutation tests, bootstrap CIs
├── part3_maintenance_conversion/           # P3: funnel, channel test, power calc
├── part4_placement_analysis.py             # P4: placement permutation tests
├── part5_campaign_experiment.py            # P5: live experiment + decision rule
├── part6_attribution.py                    # P6: creative & destination attribution
├── part7_scaleup_test.py                   # P7: pre-registered scale-up validation
├── refresh.py                              # reruns P1 & P3, resyncs the dashboard
├── requirements.txt                        # pinned; the old install line was incomplete
└── README.md
```

## How to run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 analysis.py && open dashboard.html      # P1
jupyter notebook ad_campaign_statistical_analysis.ipynb   # P2
cd part3_maintenance_conversion/notebooks && python3 analysis.py   # P3
python3 part4_placement_analysis.py             # P4
python3 part5_campaign_experiment.py            # P5
python3 part6_attribution.py                    # P6
python3 part7_scaleup_test.py                   # P7
```

The notebook has been verified to execute top-to-bottom in a clean venv. `requirements.txt` was generated from that environment — the previously documented install line was missing `ipykernel`, `scipy`, and `openpyxl`.

---

## Methodology notes

- **Revenue basis**: headline numbers use *priced, vehicle-detail-service jobs only*. Four rows are non-detail side jobs (vinyl fencing, decor change, garage organization, party planning); four more are pressure-washing, reclassified as non-detail even though the source tracker counted them as detailing.

- **⚠️ Revenue is GROSS, not net of labor.** Nearly every job is worked with a second person on a revenue split, and that cost is not modeled anywhere in this repo. This matters more than it sounds: **at a 50/50 split, any campaign under 2x ROAS loses money**, and three of the four measured creatives sit at or below 2.73x.

- **The tip-dropping error is recurring, not fixed.** Part 1 documented two rows where a `Total` cell wasn't recalculated after a tip was added. Part 6 found a third (Dr Morral, 8/7/26 — $110 + $40 logged as $110). Part 3 independently reports an $840 discrepancy against the source sheet. Every script recomputes from `job_value + tip` rather than trusting any entered total. The source spreadsheet remains unhardened.

- **Zero-result rows are included, not dropped.** In Part 4, 375 of 494 placement rows recorded spend with no results. Counted as zero rather than filtered — dropping them would overstate efficiency for placements that burned spend for nothing. Same class of error that once inflated a campaign gap to 18.6x.

- **Ad delivery was never randomized.** Meta's optimizer chose who saw what. Every demographic finding is observational; permutation testing the labels of a non-randomly-assigned sample tests whether a split is unusual given the marginals, not whether the trait causes the outcome.

---

## Part 1: Operations

29 billable detail jobs · **$4,721 gross revenue** · $162.79 average ticket

- **Saturday is the highest-revenue day** — useful for scheduling and ad dayparting.
- **Moreno Valley is the largest city by revenue.**
- **D2D has the lowest average ticket** ($118 vs $186 for Meta Ads) but near-zero acquisition cost.

## Part 2: Statistical Findings

- Filtered a 614-row Meta export to the 117 rows representing messaging-objective results. An earlier unfiltered version ranked two campaigns as top performers that were actually optimized for Profile Visits and Post Engagements. **Getting the label right mattered more than any model choice.**
- Female audiences: **$1.50/message vs $2.36** — permutation test, 10,000 resamples, **p = 0.0005**.
- Age 55+: **$1.53/message vs $2.35** — **p = 0.0015**.
- **§6 — A message isn't revenue, a booking is.** Tested whether gender predicts *booking*. **p = 0.822.** No evidence conversion differs by gender. The cheaper-per-message finding does not carry through to who pays.

> **Correction (Aug 2026):** §6 was published as p ≈ 1.0. Re-executing the notebook returned **0.822**. The conclusion is unchanged; the figure was wrong. Found by running the notebook in a clean environment rather than trusting the write-up.


### §4 — Correction: the flagship finding was an artifact

The original Section 4 reported that female audiences cost **$1.50 per message
against $2.36 for male (p = 0.0005)**, and that 55+ cost **$1.53 against $2.35
(p = 0.0015)**. The gender result was the first row of this repo's through-line
table, the stated basis for a live campaign, and the figure quoted most often.

**It does not survive verification.**

Those numbers were computed over `data/messaging_only_raw.csv`, which retains
only rows that produced at least one message — every row in it has
`Results >= 1`. The eight messaging campaigns actually span **458 rows and
$597.00**; the filter silently dropped **$284.87, or 48% of messaging spend,
that produced nothing at all.**

Cost per message computed only over units that produced a message is not cost
per message. It is cost per message *conditional on success*, which is a
different and much smaller number.

**This is the same error class Part 4 documents and rejects** — *"dropping
zero-result rows would overstate efficiency for placements that burned spend
for nothing; same class of error that once inflated a campaign gap to 18.6x."*
That rule was written in Part 4 and never applied backwards to Part 2.

#### Recomputed on the full-spend basis

| Test | Published | Full-spend | Verdict |
|---|---|---|---|
| **Gender**, female vs male | $1.50 vs $2.36, **p = 0.0005** | $3.49 vs $3.95, **p = 0.4519** | **Does not survive** |
| **Age**, 55+ vs under-55 | $1.53 vs $2.35, p = 0.0015 | $2.90 vs $4.52, **p = 0.0097** | **Survives** |
| Account cost per message | $1.96 | **$3.75** | Was 48% understated |

Same method throughout: aggregate cost-per-message gap, 10,000 permutations,
seed 42. Reproduce with `python3 verify_section4.py`.

Age is also a clean monotone gradient across the full spend, which the
conditioned basis obscured:

| Age band | Spend | Messages | Cost/msg |
|---|---|---|---|
| 25–34 | $31.79 | 6 | $5.30 |
| 35–44 | $204.66 | 43 | $4.76 |
| 45–54 | $142.99 | 35 | $4.09 |
| 55–64 | $104.51 | 28 | $3.73 |
| **65+** | $113.05 | 47 | **$2.41** |

#### Multiple comparisons

Eight hypothesis tests across this project: gender, age, three placement
contrasts, §6 conversion, Part 3's channel test, and Part 8's message-count
test. No family-wise correction was applied anywhere, which is itself a gap
this correction closes.

Bonferroni threshold at α = 0.05 over eight tests is **0.00625**. Age
(p = 0.0097) does not clear it; Stories vs Reels (p = 0.0004) and Part 8's
message-count result (p < 0.0001) do. Age should be treated as suggestive,
not established.

#### What changed downstream

- The live campaign built on the gender finding was **retargeted around age**.
- `ceramic_coating_campaign_tracker.xlsx` benchmarks ("$1.50/msg", "$2.02/msg")
  are conditioned figures roughly 2x cheaper than reality. True full-spend:
  August Camp **$3.23**/msg, New Engagement **$3.51**/msg.
- §6's conclusion is unaffected — it already found gender does not predict
  booking (p = 0.822). §6 was right for a reason §4 could not see: the cost
  advantage it was testing did not exist.

#### Why this correction is in the README rather than quietly patched

The claim this repository makes is that its figures are verified. A
verification process that never overturns your best result is not a
verification process. This one overturned the headline, using a standard the
project had already written down for itself.

## Part 3: Maintenance Conversion

*Verified — all figures reproduce.*

- **The leak isn't rejection, it's silence.** Of 24 candidates pitched, **46% never responded.**
- **D2D converts at 29% (n=7) vs Meta Ads' 20% (n=15)** — inverted from what ticket size predicts.
- **p = 1.000.** With 7 D2D candidates the observed 8.6-point gap is the smallest possible non-zero outcome the data could produce.
- **Power calculation: ~389 pitched candidates per channel** for 95% confidence / 80% power. D2D would need 56x its current sample.

## Part 4: Placement Efficiency

Tested a hypothesis I had **already acted on**. Jun 15 – Aug 21, $752.68, 186 messages, 456 rows with spend.

| Comparison | Cost per message | p |
|---|---|---|
| Feed vs **Reels** | $4.47 vs **$3.46** | 0.205 |
| Feed vs Stories | $4.47 vs $8.03 | 0.058 |
| **Reels vs Stories** | **$3.46** vs $8.03 | **0.0004** |

- **Reels is the cheapest placement and carries 58% of message volume.** I had excluded it. That was reversed.
- **Stories is genuinely expensive** and stays excluded.
- **This cannot answer the quality question** — the placement export has no bookings.

## Part 5: Campaign Mechanism Experiment

Two arms running simultaneously: Messenger conversation vs instant form with a 15-minute callback.

| Arm | Spend | Events | **Bookings** | **Cost/booking** |
|---|---|---|---|---|
| Messages | $95.01 | 58 msgs | **0** | — |
| Leads (form) | $20.72 | 3 leads | **1** *(tentative)* | **$20.72** |

Four variables differ between arms (objective, age range, Stories placement, response speed). `part5_campaign_experiment.py` contains an explicit confound audit and a **pre-registered decision rule**: 14 days or $100 per arm, judged on cost per booking only, act on the winner even without significance.

## Part 6: Creative & Destination Attribution

The dataset Parts 4 and 5 both lacked. **Lifetime Meta spend: $785.00.**

| Creative | Bookings | Revenue | Spend | Cost/booking | ROAS |
|---|---|---|---|---|---|
| **Save 2007 Chevy** | 4 | $590 | $72.14 | **$18.04** | **8.18x** |
| Denise Reactions | 2 | $380 | $139.04 | $69.52 | 2.73x |
| August Broad | 1 | $180 | $113.13 | $113.13 | 1.59x |
| Patrick Ads | 1 | $170 | $130.00 | $130.00 | 1.31x |
| *Unattributed* | *6* | *$1,195* | *$330.69* | *$55.12* | *3.61x* |

**7.2x spread.** Problem-specific creatives — a 2007 Chevy interior restoration, pet hair removal — massively outperform broad detailing ads. **At a 50/50 labor split, anything under 2x ROAS loses money**, which means only Save 2007 Chevy is meaningfully profitable.

> **Correction — ROAS was wrong on both ends.** Five jobs tagged `Meta Ads` were logged as organic Instagram DMs with no ad involved ($1,010 of $3,525), and the denominator understated spend. **Real ad-attributed ROAS is 3.20x ($2,515 / $785.00) against a published 5.23x — 63% too high.** After the labor split, advertising nets roughly **+$472.50** lifetime.

> **Correction — the benchmark.** Part 5's decision rule rested on "$26.09 per booking" from 5 *recalled* bookings. The log shows 2, and the creative ran twice ($42.84 + $96.20). True cost per booking: **$69.52.**

**Platform:** Instagram Ads ($189.55 average ticket, 11 jobs) beat Facebook Ads ($143.33, 3 jobs). The single highest-ticket job in the account — a $360 ceramic coating — came from **organic** Instagram, no ad.

## Part 7: Scale-Up Validation (pre-registered)

The first analysis here where the prediction is written down **before** the money is spent.

Save 2007 Chevy's $18.04/booking rests on **four events**. The exact 95% interval runs **$7.04 to $66.19** — a 9.4x span. At $280 that's anywhere from 4 to 40 bookings.

Two pre-registered hypotheses: **H1**, that observed cost per booking at scale falls inside the prior interval; **H2**, that cost rises in the back half as the cheapest audience saturates. Staged, with an interim stop at $120 if cost per booking exceeds $36.

**Capacity constraint, recorded in advance:** historical throughput is 3.6 detail jobs/week. The point prediction is 15.5. Capacity may bind before spend does, which would understate the creative. Declined and delayed jobs must be logged or H1 measures the calendar instead of the ad.

---


## Part 8: Conversation Depth and Booking

Every prior significant result in this project was a **cost** finding that
died at the booking stage. This one is the booking stage.

116 inbound leads, Jul 11 – Aug 23 2026, each hand-labelled from the actual
message thread with an outcome and a message count.

| | n | mean messages | median |
|---|---|---|---|
| **Booked** | 16 | **19.9** | 19.5 |
| Not booked | 100 | 5.5 | 4.0 |

**Gap of +14.3 messages. Permutation test, 10,000 resamples, p < 0.0001.**
Not one shuffle produced a gap that large.

| Messages | Leads | Booked | Rate |
|---|---|---|---|
| 0–5 | 62 | 0 | **0%** |
| 6–9 | 22 | 2 | 9.1% |
| 10–14 | 17 | 2 | 11.8% |
| **15+** | **15** | **12** | **80%** |

Above fifteen messages, four in five close. Below it, conversion is low and
unstructured — the 1-2 and 6-9 bands each hold one or two bookings, so the
threshold is a jump at 15, not a clean floor beneath it. Updated Aug 24 as
out-of-sample bookings landed; the permutation result held at p < 0.0001.

### This reverses Part 3

Part 3 concluded *"the leak isn't rejection, it's silence"* from 46%
non-response on n = 24. At n = 116, non-response is **19.8%**. The dominant
failure mode is **`quoted_no_book` at 56%** — leads that engaged, received a
price, and stalled mid-conversation. Part 3's finding was a small-sample
artifact; this is the correction.

### Limitations

- **Correlational.** Intent drives both message count and booking. Message
  count is partly an effect of wanting to book, not only a cause of it.
- **`Message_count` excludes phone calls.** Two booked leads moved to a call
  after ~6 messages and are undercounted; they are the 6–9 band's 2 bookings.
- **Outcomes were hand-labelled by the operator**, who knew which leads booked.
- Survives Bonferroni across all 8 project tests (threshold 0.00625) — one of
  only two results that does.

Run: `python3 part8_conversation_depth.py`

## Current Status

*Last verified: August 23, 2026*

- **29 detail jobs · $4,721 gross revenue · $162.79 average ticket**
- **Meta Ads: $785.00 lifetime spend → $2,515 ad-attributed revenue → 3.20x ROAS** *(gross; ≈ +$472.50 after labor)*
- **Best creative: Save 2007 Chevy at $18.04/booking, 8.18x** — 7.2x better than the worst
- **Maintenance: 21% positive rate; D2D ahead of Meta Ads but p = 1.000**
- **Placement: Reels cheapest ($3.46/msg); Stories worst ($8.03, p = 0.0004)**
- **Live: leads arm 1 booking on $20.72; messages arm 0 on $95.01 across 58 messages**

## Known gaps

The honest limits on everything above.

1. **Labor cost is unmodeled.** Every figure is gross. At a 50/50 split the 2x ROAS line is the real break-even, and most creatives sit near it.
2. **$330.69 of spend is unattributed** between Pet Hair Removal and an unnamed Facebook creative. Pet Hair has the highest average ticket in the account ($255) and its efficiency is still unmeasured. **Highest-value fix outstanding.**
3. **Creative attribution is self-reported from customer conversation**, not click-tracked. Last-touch by recall.
4. **Ad delivery was never randomized.** All demographic findings are observational.
5. **n is small everywhere.** 14 ad-attributed bookings total; 4 on the best creative.
6. **Six published figures have failed verification** in the last week. Every claim in this README has now been re-executed from source, but the base rate suggests continued checking.

## Next steps

- Split the $330.69 unattributed bucket. Gates gap 2 and may reorder the creative ranking.
- Add `labor_cost` to the job log and recompute contribution margin per channel.
- Log `creative_hook`, `campaign_arm`, and `placement` on every booking **at time of booking**, not from memory. Most of the failed figures trace to reconstruction after the fact.
- Rerun Part 4 on bookings-per-placement once ~20 bookings are tagged.
- Extend to a genuinely randomized experiment — two ad sets with random audience assignment — the causal design the current observational approach can't deliver.

## About me

I'm Isaac Castaneda, a UCSD student majoring in Data Science through HDSI. I built and operate Inland Auto Detailing myself; this repo is the actual analytics stack I use to run it, not a class exercise built after the fact on a public dataset. I'm interested in research opportunities that let me keep applying rigorous methods to real, messy, self-collected data.
