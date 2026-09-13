# Queue and fill mechanics

Visible depth is useful state, but does not reveal an order's identity, priority or hidden depth.
The project separated executable timing, queue scenarios and empirical calibration instead of treating
a price touch as a fill.

## Activation and the queue walk

The historical maker cell uses **50 ms POST activation and 50 ms cancellation**. Historical maker
POST observations were 24–50 ms, cancel medians 23–50 ms, and cancel p99 under load about 218 ms.
Older 250–330 ms taker-path values describe a different interval.

For placement `t0` and cancel request `tc`, the order is fillable on

$$[t_0+L_{\mathrm{post}},\ t_c+L_{\mathrm{cancel}}).$$

With initial depth ahead `r0`, own size `q`, and matched traded volume `V(t)` after activation:

$$\operatorname{filled}(t)=\min\{q,\max[0,V(t)-r_0]\}.$$

`RestingOrder` implements partial fills and the cancel race. `fill_time_brackets` is a separate
**queue-depletion** proxy: when flow reaches `r0`, without own-clip completion. The pessimistic arm
credits trades; the optimistic arm also credits unexplained visible size reductions. The former is a
subset of the latter by construction, but these are scenario bounds, not guaranteed real-fill bounds.
The caller must match prices, economic sides and trade/snapshot intervals before supplying events.

## D7: empirical curves before a parametric model

Sampling used every 50th valid book event in FULL slots, offsets 10–200 s, with a virtual touch join on
each side. State included visible depth `r0` and trailing 30-second matched volume at that side's current
touch price divided by 30:

$$\lambda_i=\frac{1}{30}\sum_{t_i-30\le u\le t_i}v_u
 \mathbf1\{\text{same price and maker side}\},\qquad x_i(T)=\lambda_iT/r_{0,i}.$$

Observation capacity `cap` is independent of fill: minimum of 20 seconds, the next same-side touch
change and the start of a structural book break. At horizon `T`, the curve is

$$\widehat F_b(T)=\frac{\sum_i\mathbf1\{c_i\ge T,x_i(T)\in b,d_i\le T\}}
 {\sum_i\mathbf1\{c_i\ge T,x_i(T)\in b\}}.$$

Short-cap samples are excluded from **both** numerator and denominator even if they filled quickly.
Keeping successful short-cap samples while discarding equally short censored samples inflates the
curve. This is a conditional fixed-capacity estimate, not Kaplan–Meier; informative censoring remains
a limitation. `empirical_fill_table` exposes that choice and rejects a reported fill after its cap.

The tested exponential hypothesis was

$$F_i(T)=1-e^{-k\lambda_iT/r_{0,i}},\qquad
\widehat k=\frac{N_{\mathrm{fill},\lambda>0}}
 {\sum_{i:\lambda_i>0}(\lambda_i/r_{0,i})[\delta_i d_i+(1-\delta_i)c_i]}.$$

Here `delta=1` denotes a fill. Zero-flow observations are excluded from the MLE and reported separately.
`fit_exponential_hazard` exposes sufficient statistics and the zero-rate count. Historical D7 starts
the queue walk at the decision instant; **it lacks the 50 ms activation correction subsequently required
by D12**. Its curves cannot be substituted unchanged for activated-order probabilities.

## Evidence and model rejection

The archived packet retains all D7 curve cells, chronological split, per-tape counts and placebo
summaries: 59,376 side observations from 867 FULL slots in blocks A+B, 84.6% pessimistic censoring,
median capacity 0.59 s. Long-horizon cells are consequently much smaller.

| T=5 s, x bucket | Eligible n | Pessimistic proxy fill probability |
|---|---:|---:|
| <0.25 | 1,905 | 0.1843 |
| 0.25–0.5 | 209 | 0.3732 |
| 0.5–1 | 131 | 0.5115 |
| 1–2 | 60 | 0.7500 |
| 2–4 | 25 | 0.8400 |
| >=4 | 17 | 1.0000 |

The last two cells fall below the historical minimum 30 for fit-quality summaries. Probabilities are
rounded archived estimates; integer fill counts cannot be recovered by rounding `p*n`.

The pessimistic MLE was `k=2.2760`, slot-bootstrap 90% interval `[2.1727,2.3839]`; optimistic
`k=5.0258`. Chronological first-70% fit was 2.2544, last-30% refit 2.3269, test weighted cell MAD 0.0415.
Stable coefficients did **not** establish trailing-flow information: permuting lambda preserved
discrimination (`0.4077 -> 0.4156`). The lambda-information hypothesis failed its placebo. Since the
ratio still contains `r0`, that test alone does not separately prove all remaining information is in
depth; the later D12 depth-permutation test supplies that additional check.

Zero trailing flow was not zero future flow: eligible zero-lambda samples filled with probability
0.2307 at 2 s (`n=945`) and 0.3810 at 5 s (`n=168`). The formula predicts zero on that subgroup.

## Reproduction contract

Definitions and inputs were fixed before the publication recheck. Run
`python estimators/mechanics_audit.py --json` to audit counts, bracket ordering, weighted discrepancies
from rounded cells and the placebo comparison. No new event-level fit or confidence interval is
claimed. `python examples/microstructure_walkthrough.py --json` demonstrates activation and censoring
with synthetic observations. Neither reruns D7's original tapes.

Sources: `d7_fill_model._grid`, `build_table`, `k_mle`, `fit_cells`, `main` and the
`d3_capture.SideWalk` queue-depletion family. See [data engineering](data-engineering.md) and
[market response](market-response.md).
