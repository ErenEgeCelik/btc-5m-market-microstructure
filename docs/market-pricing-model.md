# Market pricing model

For a driftless diffusion with constant volatility scale sigma, displacement x from an anchor and
remaining time tau, the model is p = Phi(x / (sigma sqrt(tau))). The implemented transform is
z = Phi^-1(mid) sqrt(tau), which is linear in x under that specification.

The historical pricing report records median within-slot transformed-regression R-squared near 0.92.
That is an in-sample description in transformed space. Its later held-out market-mid error is reported
at approximately six ticks RMSE. Neither number is a measurement of an identified maker's strategy.
The original logs and regression pipeline are not included here, so those empirical summaries remain
author-reported. The runnable synthetic example illustrates implementation only.

The original comparison found the market retained better outcome calibration when model and market
disagreed. Structural replication therefore did not establish alpha. Similar fitted shapes may arise
from different participant strategies; participant identity is not identified by level-2 data.

`fair.py` implements the probability map and its constant-model price diffusion.
`quote_model.py` implements the transform, inversion and a causal lagged lookup. A lagged lookup assumes
time-sorted inputs. `single_feed_series` projects multi-venue ticks to one chosen venue before signal
construction. A synchronized composite used as a pricing-model covariate is distinct from concatenating
alternating last ticks, which creates artificial jumps when venues have different price levels.

A dynamic volatility heuristic does not automatically retain the constant-model martingale property:
re-estimation, time-varying parameters and information arrival require separate treatment. Model
probabilities are not a guarantee of calibrated real-world conditional probabilities.
