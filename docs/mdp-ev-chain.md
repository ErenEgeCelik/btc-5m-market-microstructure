# Inventory accounting and EV decomposition

Let U be the Up payoff and 1-U the Down payoff. Splitting one unit of collateral creates one share
of each. Ignoring implementation costs, the pair's terminal value is U + (1-U) = 1. If both shares
are sold at a and b, the paired trading result is a+b-1, plus earned rebates and minus costs.
If only one share is sold, the remaining inventory carries outcome risk until sold, merged or resolved.

For net unhedged inventory q with conditional outcome probability p, terminal payoff variance is
q^2 p(1-p). There is no explicit time factor in this conditional expression, but p itself changes
over time and with information. This does not imply unconditional risk stays constant until expiry.

The research decomposes policy value through observable states, actions, fill events and conditional
costs. This is an MDP-inspired generative evaluation, not a claim to have solved Bellman iteration.
The accounting and EV modules make the assumptions inspectable as small functions.

For the front-policy verifier, write EV(alpha)=EV(0)-w*alpha with w>=0, where alpha is the unobserved
additional benign-fill cost and w the associated exposure weight. If EV(0)<0, every alpha>=0 is
also unfavorable within this model. The fresh-data result uses this favorable zero-cost boundary.

That monotonicity argument does not remove uncertainty in measured fill rates, eligibility, adverse
drift or costs. The interval in the aggregate evidence comes from the upstream slot-cluster bootstrap;
the public verifier reports it rather than re-estimating it.
