# Public research inputs

| Directory | Records | What can be recalculated |
|---|---|---|
| [pricing](pricing/README.md) | 358 historical slot-feature rows and source manifest | Specified scale-model fits and leave-one-log-out scores |
| [mechanics](mechanics/README.md) | Event/queue aggregates and selected recorded health intervals | Aggregate arithmetic, conditioning and health classification |
| [policy](policy/README.md) | Frozen calibration, historical summaries and all 368 common W slot outputs | Synthetic-state policy decisions and paired recorded-output comparisons |

Input selection and units are declared inside each directory. These are selected research records,
not a distribution of the complete historical tapes. The [publication manifest](../evidence/publication_manifest.json)
pins their bytes. See [Reproducibility](../REPRODUCIBILITY.md) before interpreting a rerun.
