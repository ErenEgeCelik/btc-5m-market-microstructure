# Frozen pricing-study inputs

`slot_features.json` is a JSON projection of the **entire 358-row archived June feature table**.
It preserves all original floating-point values in the selected columns. Rows are ordered by
slot time, then source group. Source groups P01–P05 preserve the original five-log partition;
they are not chronological block numbers. Source hashes and the exact field projection are in
`manifest.json`. Nothing in these files authenticates a trading account or connects to a service.

This is recorded derived data: the implied-scale fits and feed features were calculated by the
historical extractor. Running the public example recomputes regressions **from these rows**, not
from the complete raw feed/book tapes. It does not recompute the 0.919 transformed $R^2$, the
300 ms lag estimate, or the model card's 5.92-tick error. Those are identified historical reports.

The measurement and selection rules were written before the recheck in
[pricing-estimation.md](../../docs/pricing-estimation.md). In particular:

- `sigma_hat` has units USD per square-root second and is a market-implied fit target.
- `range2` and `range2_pre` are USD ranges from different windows. The first is within-slot;
  the second ends at the slot boundary. They must not be used interchangeably.
- The feature feed is the cached one-second median(Coinbase, Bitstamp, Kraken). The fitted
  displacement uses the synchronized mean(Coinbase, Binance).
- DVOL hourly-close availability is not established; flow pagination completeness is not
  established. Their regression scores are exploratory.
- Log-wise CV permits future logs in training and serves for candidate selection. It is not a
  chronological final test. No trade outcome, queue fill or P&L is inferred from this table.

Run from the repository root after installing the package:

```console
python examples/pricing_walkthrough.py
python examples/pricing_walkthrough.py --json
```

Both commands are offline and use the same fixed models. The first prints a short comparison;
the second emits all coefficients, fold counts, coefficient variability and VIFs.

`python examples/pricing_figures.py` optionally regenerates
`figures/pricing/scale_feature_audit.png` and `.svg` using matplotlib. Both scatter plots include
every row and identify acquisition groups; full-table OLS lines are distinct from the log-wise
scores in the comparison panel. No outliers are removed for presentation.
