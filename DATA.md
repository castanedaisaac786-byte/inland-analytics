# Data Dictionary & Privacy Protocol

Every file the analysis reads, every column in it, and what happens to
personally identifying information before anything is committed.

## Privacy protocol

This is a real business with real customers. Their names, phone numbers, and
addresses are never committed to this repository.

### What is removed, not obscured

**Names and phone numbers are deleted, not hashed.** A US phone number is ten
digits — an attacker can enumerate all 10^10 and match any hash in seconds.
Names in a single metropolitan service area are similarly enumerable. Hashing
these fields would be security theatre, so they are dropped entirely and
replaced with sequential identifiers.

| Field | Treatment |
|---|---|
| Customer name | Replaced with `C###` (booked) or `L###` (lead, never booked) |
| Phone number | **Deleted.** Not hashed, not truncated, not committed |
| Email | **Deleted** |
| Street address | **Deleted.** City retained — needed for the geographic analysis |
| Message content | Never captured. Only message *counts* are recorded |

### Identifier scheme

- `C001`–`C0nn` — customers who booked at least one job. Stable across every
  file, so `job_log_anonymized.csv` and `leads_anonymized.csv` join on it.
- `L001`–`L0nn` — leads that never converted. Different prefix so a glance at
  any row distinguishes customer from dead lead.

### Files that must never be committed

Enforced in `.gitignore`, prefixed with `_` so an absent-minded `git add -A`
cannot catch them:

    data/_leads_raw.csv          Meta export, contains names + phone numbers
    data/_leads_crosswalk.csv    name -> lead_id. The re-identification key
    data/_labeling_worksheet.csv working copy for manual outcome labelling
    *.pdf                        Meta reports frequently embed contact info

The crosswalk is kept locally because new leads must map to existing IDs. It
is the one file whose loss would break longitudinal analysis and whose
publication would undo the entire protocol.

`anonymize_leads.py` performs the transformation, writing the public file and
the private crosswalk in the same pass so the two cannot drift.

## `data/job_log.csv`

One row per job. The source of truth for all revenue figures.

| Column | Notes |
|---|---|
| `date` | Job date. Blank in early rows — see `tracked_period` |
| `customer` | **Anonymized to `C###` in the public copy** |
| `city` | Service location |
| `service` | Free text as written in the source tracker |
| `package_tier` | Standard / Deluxe / Premium / Interior / Maintenance / Ceramic Coating / Pressure Wash / Non-Detail |
| `n_vehicles` | Vehicles serviced on that visit |
| `channel` | Acquisition channel as originally tagged. **Unreliable** — see `ad_attributed` |
| `creative_hook` | Which ad the customer named. Self-reported |
| `platform_destination` | Instagram Ad / Instagram Organic DM / Facebook Ad / Instagram Organic Feed |
| `ad_attributed` | **1 only if a paid placement was involved.** Five jobs tagged `channel="Meta Ads"` were organic DMs with no ad. Use this, not `channel`, for any ROAS calculation |
| `campaign_arm` | Part 5 experiment arm; blank for pre-experiment jobs |
| `job_value` | Service price before tip |
| `tip` | May be blank; blank means zero, not missing |
| `logged_total` | Total **as typed into the source spreadsheet**. Never used in analysis |
| `is_detail_job` | 1 for vehicle-detail services only. Pressure washing and side jobs are 0 |
| `tracked_period` | `tracked` from 7/18 onward, `backfilled` before |

**`logged_total` vs recomputed total.** Every script computes `job_value + tip`
and treats `logged_total` as a value to *check against*, never to trust. A
source-sheet total that fails to reconcile is a known recurring error, not a
one-time bug.

## `data/ad_spend.csv`

Campaign-level Meta spend, rebuilt from the deduplicated export.

`ad_name`, `status`, `amount_spent`, `impressions`, `results`, `result_type`,
`cost_per_result`.

**Result types are not comparable across rows** — a messaging conversation, a
website lead, and a profile visit are different events. This file is a
point-in-time snapshot and goes stale; refresh before publishing any
spend-dependent figure.

## `data/placement_report.xlsx`

Meta placement breakdown, one row per day x ad x placement.

**Two traps.** The export carries subtotal rows at every breakdown level plus
exact duplicates — summing naively inflates spend roughly 6x. Filter to
`Placement == "All" AND Platform == "All" AND Device platform == "All"` for
campaign totals. And most rows have no results: they are spend that produced
nothing and must be **included as zeros**. Dropping them computes cost-per-
result over only the units that produced a result, which is not cost-per-
result. That exact error made a gender effect look significant at p = 0.0005
when the full-spend figure is p = 0.4519.

## `data/meta_ads_detailed_report.xlsx`

614 rows, day x age x gender x campaign. Columns include `Gender`, `Age`,
`Day`, `Result type`, `Results`, `Amount spent (USD)`. This is the full-spend
basis for Part 2 Section 4. `messaging_only_raw.csv` is the **conditioned**
subset of it and should not be used for any cost-per-message calculation.

## `data/leads_anonymized.csv`

| Column | Notes |
|---|---|
| `lead_id` | `C###` if booked, `L###` otherwise |
| `date` | When Meta wrote the record — **not** when contact happened. Negative lead-to-booking lags are possible and are not errors |
| `channel` | Instagram / Messenger / Phone |
| `ad_id` | Meta ad ID. Pipe-separated when a lead touched more than one ad |
| `n_ad_ids` | `>1` means last-touch attribution is a modelling choice, not a fact |
| `converted` | Matched to a booking in the job log |
| `outcome` | `booked` / `quoted_no_book` / `never_answered` / `price_objection` / `out_of_area` / `not_a_customer` |
| `Message_count` | Messages exchanged in the thread |

## Limitations that live in the data, not the analysis

1. **`channel` is unreliable** — wrong in both directions. `ad_attributed` is
   the corrected field.
2. **`creative_hook` is self-reported.** Click-level `ad_id` covers only part
   of the job log.
3. **Ad delivery was never randomized.** Every demographic comparison is
   observational.
4. **Labor cost is not in the job log.** Nearly every job is worked with a
   second person on a revenue split; every revenue figure is gross.
