# Reproduce the public calculations

The release includes reference algorithms, selected recorded features, archived mechanics
statistics and per-slot simulator outputs. Each input supports a different kind of recheck.
No command requires venue credentials, account access or a running trading system.

## Environment and commands

Use Python 3.10 or newer, from the repository root. The core package and these commands
use the standard library:

```bash
python -B examples/walkthrough.py
python -B examples/pricing_walkthrough.py
python -B examples/risk_walkthrough.py
python -B examples/microstructure_walkthrough.py
python -B examples/policy_walkthrough.py
python -B estimators/mechanics_audit.py
python -B estimators/policy_audit.py
python -B estimators/d12_public_verifier.py --check
python -B -m unittest discover -s tests -v
```

The scripts add `src/` to their import path, so installing the core package is optional.
For the optional pricing figure, install `matplotlib>=3.7`, then run:

```bash
python -B examples/pricing_figures.py
```

## What each result establishes

| Calculation | Released input | Reproduction level |
|---|---|---|
| Causal feed reference, maker activation and queue walk | Hand-authored tape and decision states | Reference algorithm behavior |
| Binary diffusion, terminal variance and CARA valuations | Declared synthetic values | Analytical identities and numerical behavior |
| Scale-feature model comparison | 358 cached slot-feature rows | Refit and leave-one-log-out scoring of archived features |
| Feed response, queue proxy and dropout summaries | Frozen historical aggregates | Arithmetic and denominator audit; no event-level reconstruction |
| Book-based policy decision | Frozen A+B calibration plus synthetic states | Corrected reference decision model, not the historical policy path |
| W policy comparison | All 368 common recorded simulator-output slots | Paired differences, descriptive time split and slot bootstrap |
| D12 rejection | Frozen estimator aggregate and decision rule | Byte-checked application of the decision rule |

The pricing folds are not chronological OOS; the winning candidate was selected on those folds.
The policy time split is descriptive within a later model-checking period. It is not a newly
untouched experiment. The archived simulation outputs retain the assumptions of their historical
producer; running the corrected public decision component does not regenerate their fills or P&L.

## Determinism, hashes and provenance

Package-specific records contain source identities, extraction rules and input SHA-256 hashes:

- [Pricing data](data/pricing/README.md) and [experiments](evidence/pricing_experiments.json).
- [Mechanics experiments](evidence/mechanics_experiments.json).
- [Policy data](data/policy/README.md) and [experiments](evidence/policy_experiments.json).
- [Publication manifest](evidence/publication_manifest.json), covering the released data and
  the historical theoretical sources used for the integrated exposition.

The W audit uses 2,000 paired slot resamples with `random.Random(17)` and linearly interpolated
5th/95th percentiles. Original archived intervals used another bootstrap implementation and need
not match the new interval bit-for-bit. Neither addresses dependence across neighboring slots.

D12 `--check` recomputes the committed verdict and byte-compares it without writes.
Its input hash remains
`428ba2de8fe47fc1e867cc8fcbee706b9fd23f16e5eceb9d8c2db1efd5c48010`.
`.gitattributes` prevents line-ending conversion of `data/` and `evidence/`, preserving all
published input fingerprints across checkouts. A hash detects a mismatch against the pinned
bytes; it does not authenticate original collection or detect coordinated input/manifest changes.

## What this package does not reconstruct

The full underlying recordings and operational engines are not distributed. The D12 event
estimation involved roughly 19 GB of recorded market data. A reader cannot regenerate its
event selection, virtual fills, placebo estimates or original confidence intervals here.
Likewise the compact pricing cache does not prove original feature availability, and the W
slot outputs do not identify real queue priority. Details accompany each experiment.

The [working draft v0.3](paper/manuscript.md) integrates the expanded pricing, mechanics and policy
methods. Its technical evidence is pinned to revision `6db010205b3aa3b8b4ee1d5715e06c47de8023b7`.
[Document build instructions](paper/README.md) describe the three figures, their provenance and
Markdown-to-PDF generation. Rebuilding the document does not reconstruct unpublished observations
or turn software validation into statistical validation.
