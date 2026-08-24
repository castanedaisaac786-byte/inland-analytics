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
