# How the pricing equation was estimated

The research separated four questions: which observed feed explains market moves, which anchor
removes a persistent basis, which link function describes the mid, and which observable features
explain the fitted scale. Each question has a different target and evaluation unit.

## Measurement contract for this release

Declared on 2026-09-14 before recomputing the published feature table. This release freezes **all
358 rows** of the existing `sigma_features.pkl` cache; it does not select favorable slots. The
published JSON retains slot time, source-log group, implied scale, within-slot range, pre-slot range,
and the previously collected DVOL and flow features. It drops absolute feed levels and operational
file names. Original and extracted byte hashes are in the dataset manifest.

The recheck fits the **seven already specified models** from `sigma_feature_select.py`, with an
intercept, ordinary least squares, and leave-one-log-out cross-validation over five source logs.
For every fold, coefficients are estimated from the other four logs and frozen before evaluating
the omitted log. The pooled score uses the mean of all held-out targets:

$$
R^2_{\mathrm{LOGO}}=1-\frac{\sum_i(\hat\sigma_i-\tilde\sigma_i)^2}
{\sum_i(\hat\sigma_i-\overline{\hat\sigma})^2}.
$$

Here $\hat\sigma_i$ is a cached market-implied scale; $\tilde\sigma_i$ is a prediction of it.
Coefficient CV is the population standard deviation divided by the absolute mean of the five
held-out-fit coefficients. VIF for feature $j$ is $1/(1-R_j^2)$ from regressing that feature on the
others with an intercept. The archived selection rule is LOGO $R^2>0.300$, first-feature coefficient
CV below 20%, and maximum VIF below 5; eligible candidates are ranked by LOGO $R^2$.

This is an **archived-feature recheck**, not regeneration of the underlying observations. LOGO
training can include later logs when testing earlier ones; it is not chronological OOS. Selecting
the winning feature set on these same folds means that the winning score is a validation score.
No new model search, chronological score, bootstrap interval, placebo, or trading result is added.

The later MDP3 clean index covers June/July booktick recordings, while these five caches concern
earlier May/June pricing sessions. No new raw-tape sample is selected here. Consequently this
feature audit does not retroactively certify the old recorder-health checks under MDP3.

## 1. Align the observed inputs before fitting

The model-card pipeline partitions books by market slot and samples them on a 50 ms grid. It keeps
the market's own bid/ask mid, records its age, excludes quotes at least 8 seconds old, and restricts
the analysis to seconds 30–270 of a 300-second slot. Missing exact boundary oracle anchors cause
slots to be excluded, even when the explanatory model uses a feed-self anchor.

Each feed is independently joined as of the recorder's arrival clock. Candidate explanatory
series include Coinbase, Binance, their synchronized mean, and a median of Coinbase, Bitstamp,
and Kraken. This is different from concatenating alternating venue ticks: the latter creates
false jumps when price levels differ. Binance alone is used for the later event-signal program.

The source compares changes in transformed mids with earlier feed changes over a lag grid and
aggregates within-slot correlations in Fisher-z space. Separate exclusive-event controls ask
whether a mid reacts when one candidate changes and the proposed alternative does not. These
observations support a feed **candidate**, not identification of a participant's private inputs.
Receiver-clock lags also include feed-specific delivery delays.

## 2. Fit the scale and diagnose the anchor

Let $x_t=F(t-\ell)-F_0$ and $z_t=\Phi^{-1}(m_t)\sqrt{\tau_t}$. Fit:

$$z_t=\alpha+\beta x_t+\epsilon_t,\qquad
\hat\sigma=1/\hat\beta,\qquad \hat\delta=\hat\alpha/\hat\beta.$$

$\hat\delta$ is a dollar displacement that compensates for the selected anchor. Since
$\alpha+\beta(F-K)=[F-(K-\alpha/\beta)]/\sigma$, the effective anchor is $K-\hat\delta$.
The historical oracle-anchor fit produced an offset near -$54; feed-self anchoring brought the
reported median close to +$0.6. That diagnoses a basis/specification problem rather than a
tradeable $54 discrepancy.

The model-card per-slot regression uses approximately one-second spacing, $0.05\le m\le0.95$,
at least 40 observations, and displacement sum of squares
$\sum(x-\bar x)^2\ge4$ dollars squared (not a $4 per-observation move).
Positive slopes map to positive scales. The family comparison
also estimates logistic and clipped piecewise-linear alternatives in the same slot. It evaluates
mid-space errors separately from transformed-space $R^2$.

`fit_transformed_schedule` in the public estimator implements the probit regression, including
the intercept and its anchor interpretation. The walkthrough's schedule example is synthetic;
its exact recovery is an arithmetic test, not a new empirical estimate.

## 3. Estimate a reusable scale rule

The original progression was:

| Version | Scale rule / target | Evaluation |
|---|---|---|
| June 12 model card | Constant scale versus $3.41+0.40\,RV_{15m}$; target is fitted market scale | Coefficients fitted on May logs; inner validation chose constant; both candidates evaluated on later logs |
| June refinement | $2.40+0.84\,RV_{2m}$, then $2.10+0.052\,R_{2m}$ | Feature comparison and five-log LOGO validation |
| June 16 feature study | Range plus DVOL and flow alternatives | Seven model candidates evaluated by LOGO; winner not independently tested |
| July A2 study | Pre-slot features predicting subsequent realized feed volatility | First-half fit, second-half evaluation; later feature selection uses that evaluation half |

For the June feature work, the cached target is fit at actual book-event times with **zero lag**,
not the model card's 300 ms lagged one-second grid. It fits $x=\mathrm{mean}(CB,BN)-F_0$ over
seconds 30–270; it requires 40 points, displacement sum of squares at least 4, and
$0.3<\hat\sigma<60$. There is no implemented book-age exclusion in this extractor. It therefore
has 358 rows rather than the model card's 340 fitted slots.

The feature source is also important: `synth1s` is a one-second **median(Coinbase, Bitstamp,
Kraken)**, built by `mm_card.load`. It is not the mean(Coinbase, Binance) used in the displacement.
The old prose sometimes called both series the same feed. This release follows the code:

- `range2`: max minus min in the inclusive interval [slot + 30 s, slot + 150 s]. This is a
  within-slot explanatory feature, unavailable at slot entry and partly contemporaneous with the target.
- `range2_pre`: the same range in [slot − 120 s, slot]. It uses information up to the boundary.
- `dvol_per_sqrt_s`: $F_0(DVOL/100)/\sqrt{365\cdot24\cdot3600}$. The collector uses an hourly
  bar's **close** at its bar timestamp; availability of that close at the slot time is not established.
  This prevents treating the DVOL improvement as a causal real-time validation.
- `ofi_30s`, `ofi_60s`, `cvd_2m`: signed Binance aggressive volume imbalance
  $(V_{buy}-V_{sell})/(V_{buy}+V_{sell})$ over trailing windows ending at the slot boundary.
  Despite the historical name, `cvd_2m` is normalized imbalance, not cumulative volume in BTC.
  The collector stops after four pages of 1,000 trades; completeness cannot be certified from
  this aggregate cache alone. Absolute-value features are computed from these cached imbalances.

The within-slot range's stronger fit than its pre-slot counterpart is useful evidence about the
model's contemporaneous structure. It does not establish the same predictability at entry.

## 4. Freeze, evaluate, and keep the target explicit

The June 12 record shows that May inner validation preferred the constant scale: median implied-scale
error 1.13 versus 1.30 for the dynamic candidate. The selected constant's later mid RMSE was 11.06
ticks. The separately evaluated dynamic candidate scored 5.92 ticks. Its coefficients were fit on
earlier logs, but choosing it after seeing that comparison uses the held-out result for selection.
The phrase “six-tick OOS replication” must preserve that qualification.

The later range rule's five-log fit must not inherit the earlier model card's six-tick score.
The June 16 report instead records 7.95 ticks for the range rule and 7.69 for range plus DVOL on
its own evaluation. That evaluation uses the full fitted feature model, partly contemporaneous
features, and repeated point-level outcomes; it is a diagnostic comparison, not untouched OOS.

Finally, a scale fitted to market quotes, realized underlying volatility, binary-price diffusion,
and probability calibration are different quantities. A better fit to one need not improve another.
The old A2 microsimulation also used 330 ms POST / 200 ms cancel assumptions, not the later maker
50/50 ms baseline. Its oracle-volatility comparison is a historical sensitivity experiment;
it cannot establish a general upper bound on the value of all alternative predictors.

See [the model and recovered results](market-pricing-model.md),
[the frozen data](../data/pricing/README.md), and
[the machine-readable experiment record](../evidence/pricing_experiments.json).
