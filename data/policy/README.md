# Policy audit inputs and fixed measurements

Declared 2026-09-14 before the public numerical recheck.

`w_slot_pnl.csv` contains every slot in the archived `links_d8.json` snapshot,
for base, REB, EVM and scrambled EVM under the `pes` fill convention. Inclusion
requires the same slot in all four variants and `FULL` in the corresponding
W01–W08 clean-index entry. No performance threshold, trimming or tape selection
is applied. Each value is the historical simulator's **cents per slot**, at a
five-share base clip; it includes modeled maker rebates and taker flatten fees.
It is a recorded simulator output, not a raw trade log or realized return.

The recheck computes arithmetic means, paired differences (EVM minus base,
REB and scrambled EVM; REB minus base), per-tape means and a chronological
70/30 descriptive split. The split is not an additional untouched test: the
whole W block is a later model-checking period. Paired 90% intervals resample
whole slots with replacement, 2,000 replicates, Python `random.Random(17)`;
linear-interpolated 5th/95th percentiles. Original intervals used NumPy, 1,000
replicates, and are retained as archived estimates. Numerical intervals need
not match bit-for-bit. Dependence between neighboring slots is not modeled.

`w_archive.json` retains reported variant summaries and explicitly distinguishes
the W snapshot from earlier D11/D15 A+B+F reports. `frozen_calibration.json`
contains A+B-only fill buckets, regime-conditioned five-second drift estimates,
joint-fill multiplier and front fill rates exported by D12. The demo uses these
recorded parameters with **synthetic decision states**. It does not regenerate
the historical W paths or fills. The exported drift is conditioned on the
decision-time regime (`R0c`), not the future-window regime used in other D12
analyses. JOIN drift/joint estimates are reused for front quotes, front-calm
fill rates for other regimes, and ten-second probabilities for variable-length
decision windows. Those transfers are modeling assumptions.

Source IDs, raw SHA-256 hashes, extraction paths and public file hashes appear
in [the policy evidence record](../../evidence/policy_experiments.json).
Only summary data and slot timestamps are released; there are no account IDs,
order instructions, credentials or operational endpoints.
