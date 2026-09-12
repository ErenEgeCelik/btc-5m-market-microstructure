# Pricing and Market Making in Short-Horizon Crypto Prediction Markets

Eren Ege Çelik · Independent researcher · Working paper, 13 September 2026

## Abstract

Short-horizon binary contracts connect a continuous underlying price to a discrete terminal payoff.
This study examines pricing structure, order-book measurement and market-making policy evaluation
in historical Polymarket BTC five-minute up/down markets. A Brownian-probit model describes broad
within-slot variation in market mids, but structural fit does not identify an individual participant's
strategy or establish profitable forecasting. Execution modeling introduces additional constraints:
venue-specific feed levels can manufacture signals when merged incorrectly, and hypothetical fills
cannot occur before order activation. A latency-corrected static front-quoting experiment produced
fresh-data expected value of −0.9845 cents per eligible decision moment, with a 90% slot-cluster
interval of [−1.626, −0.364], across 312 moments in 193 slots. The estimate is negative even with an
unobserved additional fill cost set to zero. Positive results for other replay policies remain
model-dependent, while defective paper runs support operational diagnosis rather than economic
conclusions. The accompanying repository provides reference components and verification of a decision
rule from aggregate evidence; it does not independently reconstruct the original raw-data estimates.

## 1. Research question and contribution

The motivating question is how a compact description of market prices translates into an executable
policy. A model can reproduce the broad shape of binary prices while omitting the conditional
information contained in fills, queue priority and the response of other traders to an order. Those
omissions matter most when expected spread income is small relative to adverse selection.

The research programme covers three connected questions. First, how well does a simple binary pricing
map describe observed market mids? Second, which parts of the observed feed/book relationship survive
measurement controls? Third, do policies built from those relationships retain favorable economics
after explicit activation, fill and inventory assumptions?

The contribution is an empirical and engineering case study, not a new general pricing theorem.
The selected experiments were conducted during June–July 2026 under the study's point-settlement
specification. Earlier positive results and later corrections are retained as a chronological record.
The central policy conclusion is a rejection within a defined model and historical sample, not a
claim that profitable market making is impossible.

## 2. Instrument and observation model

The studied contracts represent complementary Up and Down claims on a five-minute BTC price window.
The research treats their outcome as a comparison of reference observations at the start and end of
the window. A complementary pair has terminal payoff one dollar. The study's continuous-price model
assigns zero probability to an exact boundary tie; the actual tie convention belongs to the individual
contract specification. The public package does not yet include a complete archived rule snapshot.

The contractual reference, external spot feeds and contract book are distinct observations. A feed
can lead a displayed reference without providing executable arbitrage. A level difference between
venues can also be stable without being a forecast. The price model's feed-self anchor describes a
market-mid relationship and must not be silently substituted for the contractual resolution anchor.

Records used by the broader programme include exchange ticks, book updates and trades. Collection and
observation timestamps require separate treatment. Offline studies use as-of values and an explicit
clean-data index. The original data audit identified CLOB WebSocket freezes up to 32 seconds while
external feeds continued to move. Such intervals can resemble stable quoting opportunities unless
excluded. The public reference implementation illustrates masking; the full raw recordings are not
distributed with this manuscript [R1].

## 3. Pricing structure

Consider an idealized driftless diffusion with constant volatility scale sigma. For displacement x
from the anchor and remaining time tau, the binary probability map is

$$p(x,\tau)=\Phi\left(\frac{x}{\sigma\sqrt{\tau}}\right).$$

The transformation

$$z=\Phi^{-1}(p)\sqrt{\tau}$$

is linear in x under this specification. The historical pricing report records median within-slot
R-squared of approximately 0.92 for transformed regressions. This is an in-sample statistic in
transformed space, not a 92% directional prediction rate. A specification frozen using earlier logs
subsequently reproduced held-out market mids at approximately six ticks RMSE; one tick in this study
is one cent. These two summaries describe different evaluation views of the same pricing model [R2].

The public package supplies the transform and inversion, but not the original regression logs.
Accordingly these figures are author-reported historical estimates, not independently reproduced
results of the public demonstration. They also do not isolate a dominant maker: market mids aggregate
multiple participants and can be consistent with several underlying strategies.

The historical comparison found better realized-outcome calibration in market prices when the
model and market disagreed. This restricted the model's use to structural interpretation and timing
research. It did not support treating model-market disagreement as a profitable signal. The result
does not establish universal market efficiency outside the measured samples.

Under the ideal constant-parameter model, the induced price diffusion is

$$\sigma_p(p,\tau)=\frac{\phi(\Phi^{-1}(p))}{\sqrt{\tau}}.$$

Its interior-price behavior near expiry explains why a fixed underlying move can cause large changes
in a binary probability. It does not mean every realized path has diverging risk: probabilities may
move toward a boundary. Re-estimating volatility or using a forecast proxy also changes the assumptions
needed for a martingale interpretation. A dynamic volatility heuristic alone does not guarantee it.

## 4. Measurement and execution

### 4.1 Feed construction

A merged last-value stream alternates between whichever venue last reported. With a persistent
inter-venue price offset, it creates a sawtooth pattern even when each venue's own path is smooth.
Matched controls exposed this artifact in the original event studies. Subsequent signal construction
uses Binance alone. This differs from constructing a synchronized composite covariate for a pricing
regression: the sampling operation, not merely the number of sources, determines the artifact [R1].

### 4.2 Queue access

Level-2 observations do not reveal the queue rank of a counterfactual order. The research therefore
walks hypothetical orders through visible depth and subsequent prints. Trades-only depletion and
depletion that also credits unexplained size reductions are sensitivity scenarios. They are not
guaranteed bounds on real fills: hidden liquidity, replenishment, priority and changes caused by the
additional order are unobserved.

The historical maker decision cell uses 50 ms activation and 50 ms cancellation. Maker POST
measurements were 24–50 ms, while cancel median measurements were 23–50 ms with a longer tail under
load. Older 250–330 ms figures concern the taker path. A separate paper campaign used incorrect
execution assumptions; that comparison was subsequently invalidated [R3]. These are historical
engineering measurements, not advertised current venue service levels.

An order decided at t cannot consume prints before t plus activation delay. In the initial front
experiment, this distinction was omitted. Correcting it removed a substantial part of the apparent
edge. A cancel request likewise leaves a period of exposure before modeled removal.

## 5. Inventory and expected value

Let U denote the Up payoff. Holding q_U Up shares and q_D Down shares gives terminal value

$$q_D+(q_U-q_D)U.$$

With net inventory q=q_U-q_D and conditional outcome probability p, the conditional variance is

$$q^2p(1-p).$$

Time does not appear explicitly, but p changes with time and information. This expression must not
be interpreted as constant unconditional risk until settlement. If both shares from a split pair
are sold at a and b, the paired trading result before costs is a+b−1. If only one is sold, the remaining
inventory retains outcome risk. Historical rebates enter separately from trading income.

The research represents policy choices using states, actions, transition components and rewards.
The implementation is an MDP-inspired generative expected-value decomposition rather than a solved
Bellman control problem. It distinguishes a policy's observable fill-conditioned drift from an
additional unobserved cost parameter. With non-negative exposure weight w,

$$EV(\alpha)=EV(0)-w\alpha,\qquad \alpha\geq0.$$

A negative EV(0) rejects the candidate for all non-negative values of this additional cost within
the model. This is a sensitivity argument conditional on the other measurement assumptions. It
does not independently prove that the queue proxy, eligibility rules or estimated drift are correct.

Inventory-aware quoting has a substantial existing literature. Avellaneda and Stoikov [L1] provide
a continuous-price market-making framework; its assumptions should be re-derived for the payoff and
execution problem being studied here. Adverse selection from informed trading provides a separate
reason for spreads and fill-conditioned losses, as modeled by Glosten and Milgrom [L2]. Neither work
implies that a particular empirical implementation here is profitable.

## 6. Static front-quoting experiment

The D12 front-calm cell uses clean full slots, decision times 10–200 seconds after the window opens,
and paired samples every 50 book events. Calm is defined from Binance's as-of 1.5-second displacement
with absolute magnitude below three dollars. Two-sided improvement requires a spread of at least
three cents, so improving each side by one tick does not create a locked quote. These are historical
definitions of the evaluated candidate, not parameters selected for current trading [R3].

Fills start after 50 ms activation. The front proxy uses subsequent side-matched prints while the
improved level remains available, capped by a primary horizon of ten seconds. The recorded book's
arrival at the improved level closes this opportunity window. Because the hypothetical improved
level did not necessarily exist on tape, its fill process has counterfactual uncertainty. Dropouts
and missing or stale future marks remove affected samples. The public verifier does not rerun that
event-level construction.

The original protocol includes chronological evaluation, queue and regime permutation controls,
slot-cluster bootstrap intervals and stability checks. Protocol existence alone is not evidence that
every individual study passed every check. The public D12 summary includes the selected control
outputs, but confidence intervals and placebo estimates are reported from the upstream estimator.

| Sample or sensitivity | EV(0), cents per eligible moment |
|---|---:|
| Discovery block A | +0.3383 |
| Discovery block B | +0.4325 |
| Grown fresh block F | −0.9845 |
| Fresh 90% slot-cluster interval | [−1.626, −0.364] |
| Chronological final 30% | −0.9989 |
| Fresh result after the most favorable single-slot omission | −0.8792 |

The fresh result covers 312 eligible moments in 193 slots. Moments are not treated as independent
observations for interval construction; the reported uncertainty unit is the slot. The chronological
split and fresh block are related checks and should not be counted as independent replications.
The grown fresh result supersedes earlier estimates on a smaller fresh sample [R4].

The interval is entirely negative at alpha zero. A single omitted slot does not restore the sign.
The resulting decision is to reject this static policy within its represented assumptions. The
public command `python -B estimators/d12_public_verifier.py --check` verifies that this decision agrees
with the committed aggregate input. It does not rebuild the sampling distribution.

## 7. Other policies and the limits of paper comparison

Inventory rebalancing and decision-time EV policies produced positive replay comparisons under their
declared controls. Those findings remain model-dependent upper bounds because visible historical
flow does not reveal the response to our own orders. They are part of the research record, but no
live-profitability estimate is inferred from them [R3].

A separate diagnostic aligned replay with a six-slot stress window observed by a paper engine.
Replay credited approximately +$21 while the paper engine reported approximately −$31. Investigation
identified cold-start regime blindness, stale-feed handling and inventory/loss-limit defects.
The comparison demonstrates an implementation and model-coverage gap. Because the paper run was
defective, it supports no economic conclusion about a correctly functioning strategy [R5].

An earlier 157-slot A/B comparison is a distinct experiment. Subsequent inspection found incorrect
execution assumptions and invalidated its economic interpretation. The corrected research record
therefore does not retain its old inconclusive label as evidence from a clean comparison. Aligning
time windows is necessary for comparison but insufficient when engine mechanics differ.

## 8. Reproducibility and limitations

The repository offers three inspectable layers: mathematical reference functions, a synthetic event
walkthrough, and a deterministic decision-rule verifier over aggregate output. The component suite
contains 62 tests. These checks establish implementation behavior and agreement with stored evidence;
they do not authenticate the original observations or independently validate empirical estimates.

The main limitations are unpublished raw-data reconstruction, inferred queue priority, counterfactual
execution response, limited historical regimes and incomplete archived instrument rules. Multiple
experiments informed the research sequence, so a clean fresh split should not be mistaken for a fully
preregistered programme with no researcher adaptation. The final policy is specified explicitly to
avoid extending its rejection to untested families.

The owner reports a subsequent change toward averaging in settlement. This paper makes no exact
transition-date or weighting claim and does not transfer point-settlement results to that payoff.
Archived primary rule evidence would strengthen the historical specification without requiring a new
strategy study. Further empirical reconstruction could also improve independent reproducibility.

## 9. Conclusion

The historical price process admitted a useful compact description, while executable policy value
depended on additional assumptions about activation, queue access, selection and inventory. Corrected
measurement rejected the specified static front policy on fresh data. Other positive replay findings
and broken paper comparisons did not establish live profitability. The resulting research package
separates structural modeling, empirical summaries and operational diagnosis so that each can be
reviewed at the level of evidence it actually provides.

## References and research artifacts

- **[L1]** Avellaneda, M. and Stoikov, S. (2008). *High-frequency trading in a limit order book*.
  Quantitative Finance, 8(3), 217–224. [Author-hosted paper](https://math.nyu.edu/inmemoriam/avellaneda/HighFrequencyTrading.pdf).
- **[L2]** Glosten, L. R. and Milgrom, P. R. (1985). *Bid, Ask, and Transaction Prices in a Specialist
  Market with Heterogeneously Informed Traders*. Journal of Financial Economics, 14(1), 71–100.
  [Columbia research record](https://business.columbia.edu/faculty/research/bid-ask-and-transaction-prices-specialist-market-heterogeneously-informed-traders).
- **[R1]** Author research records, D0/D4 data and feed studies. Public method summary:
  [queue and fill mechanics](../docs/queue-and-fill-mechanics.md). Raw recordings not included.
- **[R2]** Author pricing research report, June 2026. Public summary:
  [market pricing model](../docs/market-pricing-model.md). Original regression logs not included.
- **[R3]** Author D12 methods and chronological research log, July 2026. Public summaries:
  [EV decomposition](../docs/mdp-ev-chain.md) and [experiment revisions](../docs/negative-results.md).
- **[R4]** [D12 aggregate estimator output](../evidence/links_d12.json) and
  [verified decision summary](../evidence/d12_public_verdict.json). The summary records its input SHA-256.
- **[R5]** Author D16 and A/B audits, July 2026. Public summary:
  [replay and paper coverage](../docs/simulation-coverage.md). Original paper journals not included.

## Author and development note

The research is by Eren Ege Çelik. AI coding and writing assistants were used in implementation,
documentation and preparation of this working manuscript. The manuscript is offered for feedback
and has not been peer reviewed. Questions about the model assumptions, empirical identification
and reproduction boundary are especially welcome.
