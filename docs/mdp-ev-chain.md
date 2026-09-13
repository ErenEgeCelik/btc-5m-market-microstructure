# From inventory state to branch EV

The research translated a maker's operational sequence into measured components:
choose a book level, wait for activation, face fills and cancellation races,
manage a remaining leg, then flatten. Two implementations resulted: an MDP2
generative policy evaluator and a later D15 one-step EV selector embedded in a
stateful inventory replay. Neither implemented a full Bellman optimizer.

## State, actions and the distinction from a solved MDP

The proposed state was $S_t=(R_t,Q_t,I_t,T_t)$: regime, outstanding quote state
and placement, signed inventory, and slot phase. Book spread, wall size and
trailing side-specific flow supplied additional conditioning variables.
Actions included posting, holding or cancelling each side, choosing JOIN or
one-tick improvement, and flattening. Event-driven transitions made the design
semi-Markov in spirit. A full finite-horizon formulation would require

$$
V_t(s)=\max_a E[r(s,a,S_{t'})+V_{t'}(S_{t'})\mid S_t=s,a],
$$

including inventory-dependent future value and the distribution of the next
event time $t'$. The implemented EVM instead evaluates the next quoting
decision using frozen fill/drift inputs, then applies inventory constraints.
It does not estimate that continuation value. Its running cash/inventory ledger
makes the replay stateful; that alone does not turn a greedy policy into dynamic
programming. [The implemented policy](strategies.md) names each actual step.

## Split-pair accounting and price coordinates

Let $U\in\{0,1\}$ be the Up outcome. One split pair pays
$U+(1-U)=1$ dollar. Selling Up at $a$ dollars and Down at $d$ dollars yields
$a+d-1$ dollars per completed pair before rebates and costs.

The replay uses synthetic Up-book coordinates in **cents**: $q_A$ is an Up ask
and $q_B=100-q_D$ is the equivalent Up bid from selling Down at $q_D$ cents.
Consequently the matched spread is

$$s=q_A-q_B=q_A+q_D-100.$$

An A fill reduces signed Up exposure; a B fill increases it. The synthetic
ledger writes A proceeds as $+q_A n_A$ and B as $-q_B n_B$. The latter includes
the split collateral transformation: it is not a claim that selling Down has
negative cash proceeds. Matched pairs cancel that collateral baseline.
After all unmatched exposure is flattened, the synthetic and split-inventory
accounting agree. [Binary risk and market making](binary-risk-and-market-making.md)
separates the terminal inventory calculation from diffusion-based risk penalties.

## Four fill branches

For one paired unit, let $A=P(F_A)$, $B=P(F_B)$ and $J=P(F_A\cap F_B)$.
The branch probabilities must satisfy

$$
\max(0,A+B-1)\le J\le\min(A,B),\qquad
(p_{AB},p_A,p_B,p_0)=(J,A-J,B-J,1-A-B+J).
$$

The model uses an empirical multiplier $\rho$ and projects $AB\rho$ onto this
interval. The frozen calibration has $\rho=1.036$. This is a fitted joint-fill
adjustment, not a correlation coefficient. Independence sets $J=AB$;
conditioning on regimes does not imply any universal sign for the difference
between $E[A_RB_R]$ and $E[A_R]E[B_R]$.

For decision-time book mid $m$, define $\delta_A=q_A-m$ and
$\delta_B=m-q_B$. Prices are selected **from the book**; these are diagnostic
edges relative to its mid, not quotes centered on model fair value.
Let $r_A,r_B$ be historical maker rebates in cents/share. Let
$\Delta_A=m_{\mathrm{fill}+5s}-m$ and
$\Delta_B=m-m_{\mathrm{fill}+5s}$ denote signed, fill-conditioned drift.
Then the one-leg identity $\delta+r-\Delta$ equals mark-to-mid trading value
plus its rebate. Adding a quote-price markout to $\delta$ again would double
count the spread.

| Outcome | Weight | Reward, cents per paired unit |
|---|---:|---|
| Both fill | $J$ | $s+r_A+r_B$ |
| Only A fills | $A-J$ | $\delta_A+r_A-\Delta_A-\alpha$ |
| Only B fills | $B-J$ | $\delta_B+r_B-\Delta_B-\alpha$ |
| Neither fills | $1-A-B+J$ | $0$ |

Thus

$$
E_2=J(s+r_A+r_B)+(A-J)(\delta_A+r_A-\Delta_A-\alpha)
 +(B-J)(\delta_B+r_B-\Delta_B-\alpha).
$$

For a single-side action the marginal value is
$E_A=A(\delta_A+r_A-\Delta_A)$ or
$E_B=B(\delta_B+r_B-\Delta_B)$. These action values do not add in general:
two filled complementary legs eliminate the unmatched drift channel.
Multiplying $E_2$ by a common five-share clip gives cents per decision;
division by 100 gives dollars. It does **not** give cents per slot without
the number and interaction of decisions. The historical function name
`slot_ev_cents` is preserved for compatibility but computes one paired decision.

## Fill probability, drift and hidden cost are separate inputs

Historical JOIN lookup uses $x=\lambda H/r_0$ with $H=10$ seconds, visible wall
$r_0$ in shares and past 30-second side/price-specific flow $\lambda$ in
shares/second. A table maps $x$ to fill probability. The exponential
$1-\exp(-kx)$ was investigated, but its trailing-flow discrimination failed a
permutation control and it overpredicted in middle buckets. The public selector
uses the recorded empirical table. Retaining a composite $x$ bucket does not
establish incremental predictive value of $\lambda$ over $r_0$.

Front fill probability came from a separate hypothetical improvement model.
Its level and queue access were not present in the tape, and the lifetime
ended when an actual book improvement occupied the level. These are model
conventions rather than observed fills of an order we placed.

The unknown additional cost $\alpha\ge0$ enters unmatched fills only:

$$E(\alpha)=E(0)-w\alpha,\qquad w=A+B-2J\ge0.$$

For $E(0)>0,w>0$, the zero is $\alpha^*=E(0)/w$. If $E(0)<0$, increasing
$\alpha$ cannot rescue this fixed model. This was D12's favorable-boundary
rejection argument. Uncertainty in eligibility, drift and fill probabilities
still matters; a negative estimate is not by itself statistical certainty.
The [D12 verifier](../estimators/d12_public_verifier.py) audits stored decision inputs;
the [policy audit](../estimators/policy_audit.py) additionally recomputes paired
intervals from released simulator-output rows.

## What the older generative chain added

MDP2's `Chain` evaluated policy specifications with separate families for the
submit-to-fill funnel, front episodes, altered adverse-fill mixtures, scaled
exposure and reactive stop losses. LinkStore supplied measured estimates and
uncertainty ranges; explicitly unknown parameters could be swept separately
to rank sensitivity. The reported $P(EV>0)$ was a Monte Carlo frequency **under
those assumed input distributions**, not a calibrated posterior probability of
profitability. The proposed semi-Markov state description was richer than these
implemented family-specific generators.

A reconciliation gate asked whether the as-operated generator reproduced the
same run's landed orders, fills, shares and loss before testing alternatives.
That run had 78.4% balance rejects: matching it was a mechanics check, not
economic validation. Its useful contribution was identifying missing funnel,
one-sided inventory and adverse-fill mixture terms before interpreting EV.

Source versions and symbol names are recorded in
[policy provenance](../evidence/policy_experiments.json). Public joint weights
include the missing Fréchet lower bound; the historical result rows are retained
unchanged and must not be attributed to a rerun with that correction.
