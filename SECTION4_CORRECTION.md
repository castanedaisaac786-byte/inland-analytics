<!-- Replaces the Part 2 §4 bullets in README.md, and belongs as a markdown
     cell at the top of Section 4 in the notebook. -->

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
