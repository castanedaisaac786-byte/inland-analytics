<!-- Three additions the audit asked for. Paste each into README.md where
     indicated. -->

---
<!-- (1) Into Methodology notes -->

- **Permutation tests assume exchangeability that Meta's optimizer violates.**
  Parts 2 and 4 permute labels across day × cell reporting rows whose spend
  Meta *allocated in response to performance*. Under a true null, rows are
  therefore not exchangeable — the algorithm shifts budget toward whatever is
  working, and within-day and within-ad correlation is unmodeled. This is a
  distinct problem from non-randomized delivery and is not fixed by the
  observational caveat above. It means p-values here should be read as
  descriptive of how unusual a split is given the observed marginals, not as
  calibrated error rates.

- **Multiple comparisons.** Eight hypothesis tests across this project:
  gender, age, three placement contrasts, §6 conversion, Part 3's channel
  test, and Part 8's message-count test. No family-wise correction was
  applied during analysis. Bonferroni at α = 0.05 over eight tests gives a
  threshold of **0.00625**. Two results clear it: Stories vs Reels
  (p = 0.0004) and Part 8's message-count effect (p < 0.0001). Age
  (p = 0.0097) does not, and is treated as suggestive rather than
  established.

---
<!-- (2) Into Part 5, before the arms table -->

**Prior attempt, disclosed.** This is not the account's first lead-form
campaign. In August a campaign called `big camp` ran the same objective for
**$51.05 and produced one lead — a test submission I made myself.** The
tracker's own verdict at the time was "avoid repeating this setup." Arm B is a
second attempt at a mechanism that has already failed once here, and any read
of its performance should carry that.

---
<!-- (3) Into Part 6, after the creative ranking table -->

**The spread is a ranking of point estimates, not an established difference.**
Exact Poisson 95% intervals on cost per booking overlap almost completely:

| Creative | Bookings | Point | 95% interval |
|---|---|---|---|
| Save 2007 Chevy | 4 | $18.04 | $7.04 – $66.19 |
| Denise Reactions | 2 | $69.52 | $19.25 – $574 |
| Patrick Ads | 1 | $130.00 | $23.33 – $5,135 |

With intervals this wide, "7.2x spread" describes the point estimates and
nothing more. The licensed claim is that **creative is the most promising
lever to test next** — which is what Part 7 was built to do, and why it is
pre-registered rather than reported as a finding.
