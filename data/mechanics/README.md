# Frozen mechanics inputs

The publication contract and formulas are in [data engineering](../../docs/data-engineering.md),
[market response](../../docs/market-response.md) and [fill mechanics](../../docs/queue-and-fill-mechanics.md).
Selection was fixed before the publication numerical recheck. All files are local research records;
no new exchange requests were made.

| Packet | Included content | Reproduction level |
|---|---|---|
| `b05_health_excerpt.json` | First eight chronological B05 indexed slots, tape bounds, anchor flags and overlapping book gaps | Recompute eight health classes and coverage values; reported whole-tape statistics remain archived |
| `links_d4.json` | Entire archived D4 output, threshold rows and placebo | Aggregate arithmetic only; no event rows or placebo n |
| `links_d4b.json` | Entire D4b output, magnitude buckets, horizon-specific n, counters and per-tape counts | Recompute transfer ratios from rounded means and sample accounting |
| `links_d7.json` | Entire D7 output, empirical curves, fit cells, coefficients, OOS, placebo, tape counts | Recompute rounded-cell weighted discrepancy, counts and bracket consistency; no new fitting |
| `links_d14.json` | Entire D14 output, time-bin means, thresholds, block rows, reported intervals | Recompute flow ratios and count reconciliation; medians/event-percentage CIs are reported only |

Run `python estimators/mechanics_audit.py --json` from the repository root. Byte hashes and source
function mappings are in [mechanics_experiments.json](../../evidence/mechanics_experiments.json).
The health index is a later merged registry; the frozen aggregate experiments retain their original
universes (for example, D7's A+B 867 FULL slots). It would be incorrect to assume every file used the
latest full registry. D4b and D7 record A/B tape counts; D14 records A/B/F block counts without per-tape
rows. Missing granularity is not reconstructed from prose.

Confidence intervals are historical 90% slot-cluster bootstrap outputs where reported. Original
cluster observations are absent, so this compact release does not regenerate those intervals.
English documentation explains legacy keys such as `kovali` (bucketed observations). No fill counts
are manufactured from rounded probabilities. No reconstructed raw tape is presented as recorded data.
