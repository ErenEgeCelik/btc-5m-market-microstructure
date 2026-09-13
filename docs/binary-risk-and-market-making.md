# Binary risk and the market-making decision

The research connects a model of the underlying price to the risk of an unmatched binary
position. This page derives that connection and distinguishes inventory valuation from an
executable policy. The historical policy uses book prices, empirical fill estimates and an
inventory constraint; it does not solve an Avellaneda–Stoikov control problem.

## Three different volatility quantities

Write the ideal underlying as $dF_t=\sigma_F dW_t$, with constant $\sigma_F$ in
dollars per square root second. For a fixed strike $K$, remaining seconds $\tau=T-t$,
and a one-dollar payoff $X=\mathbf{1}_{F_T>K}$:

$$
p_t=u(F_t,t)=\Phi(z_t),\qquad z_t=\frac{F_t-K}{\sigma_F\sqrt{\tau}}.
$$

This is a conditional probability under the stated driftless model. Calling an empirically
fitted market-price scale $\widehat\sigma$ a physical volatility would add an assumption.
The [pricing study](market-pricing-model.md) examines the distinction.

For the ideal matched constant-volatility model,

$$
u_F=\frac{\phi(z)}{\sigma_F\sqrt{\tau}},\qquad
u_{FF}=-\frac{z\phi(z)}{\sigma_F^2\tau},\qquad
u_t=\frac{z\phi(z)}{2\tau}.
$$

Itô's formula cancels the drift $u_t+\tfrac12\sigma_F^2u_{FF}$ and gives

$$
dp_t=\underbrace{\frac{\phi(\Phi^{-1}(p_t))}{\sqrt{\tau}}}_{\sigma_P(p_t,\tau)}\,dW_t.
$$

The underlying's scale cancels in this expression **at a given probability**. It still
determines the mapping from $F_t-K$ to that probability. Binary-price diffusion, measured in
contract dollars per square root second, increases near the strike as expiry approaches.
At $p=0.5$, shortening $\tau$ from 100 seconds to one second multiplies it by ten.

Plugging a fitted, stochastic $\widehat\sigma_t$ into $\Phi$ does not inherit the drift
cancellation. Parameter changes introduce additional terms and potentially covariation.
For a known deterministic volatility schedule, the appropriate remaining variance is
$V_t=\int_t^T\sigma_F(s)^2ds$, giving diffusion
$\phi(\Phi^{-1}(p_t))\sigma_F(t)/\sqrt{V_t}$.

## Split inventory and terminal variance

With $q_U$ UP shares, $q_D$ DOWN shares, and cash $c$, settlement wealth is

$$
W_T=c+q_D+I X,\qquad I=q_U-q_D.
$$

Consequently,

$$
\mathbb E_t[W_T]=c+q_D+I p_t,\qquad
\operatorname{Var}_t(W_T)=I^2p_t(1-p_t).
$$

Matched pairs have a certain one-dollar payoff; unmatched inventory carries the settlement
risk. At a fixed probability there is no additional maturity multiplier in this variance.
Risk is not constant along a price path: $p_t$ changes, and typically approaches zero or one
at settlement. Under the ideal model, Itô isometry reconciles the local diffusion and the
terminal variance:

$$
\mathbb E_t\!\left[\int_t^T\sigma_P(p_s,T-s)^2ds\right]=p_t(1-p_t).
$$

This is why replacing integrated future binary variance by today's diffusion squared
times remaining time is generally unjustified.

## Comparison with Avellaneda–Stoikov

Avellaneda and Stoikov model a Brownian mid-price, exponential utility and order-arrival
intensities. Their frozen-inventory reservation center is

$$
r=s-q\gamma\sigma_S^2(T-t).
$$

The reservation valuation and the execution quotes are separate steps; execution also
depends on arrival intensities. See their equations (6)–(8), (13)–(19) in
[High-frequency trading in a limit order book (2008)](https://math.nyu.edu/inmemoriam/avellaneda/HighFrequencyTrading.pdf).

The following binary calculation uses the same exponential-utility idea with a Bernoulli
terminal payoff. It is an explanatory derivation added for this publication, not a claim
that the historical bot implemented their optimizer.

For net inventory $I$ and risk aversion $\gamma>0$ in inverse dollars, define

$$
M(I)=1-p+p e^{-\gamma I},\qquad C(I)=-\frac{1}{\gamma}\log M(I).
$$

$C(I)$ is the exact certainty equivalent of $IX$. The one-share indifference values are

$$
b(I)=C(I+1)-C(I),\qquad a(I)=C(I)-C(I-1).
$$

For small $\gamma$ at fixed finite inventory,

$$
C(I)=Ip-\frac{\gamma}{2}I^2p(1-p)+O(\gamma^2),\qquad
\frac{a(I)+b(I)}2=p-\gamma I p(1-p)+O(\gamma^2).
$$

Thus $p-\gamma I p(1-p)$ is a small-risk-aversion inventory-valuation approximation.
It is not an exact finite-inventory quote formula or an arrival-rate calibration.
At $p=0.5$, $I=0$, $\gamma=0.1$, the exact values are approximately $b=0.487505$ and
$a=0.512495$. Long UP exposure lowers both values. A book tick, queue priority, cancellation
delay and balance constraints can make either value unavailable as an executable order.

## What the historical implementation actually does

The [EV decision model](mdp-ev-chain.md) compares book-derived actions through their
none/one/both-fill outcomes. [Policies](strategies.md) combine this one-step estimate with
inventory rebalancing, directional exclusions and terminal handling. The state and transition
tree organize the decision problem; the extracted implementation is not a solved Bellman recursion.

The practical connection is the cost of unmatched exposure: conditional price drift, fill
dependence and inventory handling must enter the accounting. The public theory helpers do not
replace those empirically tested mechanisms with a theoretical reservation center.

## Inspect the calculation

```bash
python -B examples/risk_walkthrough.py
```

- [`fair.py`](../src/btc5m_research/fair.py): probit probability and ideal binary diffusion.
- [`risk.py`](../src/btc5m_research/risk.py): terminal moments and exact frozen-inventory values.
- [`test_binary_risk.py`](../tests/test_binary_risk.py): both settlement outcomes, utility
  indifference, inventory skew, risk-neutral limits and numerical stability.

Historical derivation source: private `whitepaper/09_theory.md` and the Brownian-pricing
notes. This exposition corrects their overbroad wording about time-invariant risk and distinguishes
the approximation from the exact utility calculation. No empirical return is inferred here.
