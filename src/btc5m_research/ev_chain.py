"""Expected-value decomposition for one quoting decision.

Per decision window the policy ends in exactly one of four states, and the EV is
the probability-weighted sum over them::

    EV = A*B*rho * (spread + 2*rebate)            both legs fill -> flat
       + A*(1-B) * (edge_a + rebate - drift_a)    one leg fills -> position held
       + (1-A)*B * (edge_b + rebate - drift_b)
       + (1-A)*(1-B) * 0                          nothing fills

``A`` and ``B`` are per-side fill probabilities, and ``rho`` corrects their product
for the fact that the two legs are **anticorrelated**: the move that fills one side
pulls price away from the other. Measured joint completion was 0.36 against a
product of 0.45, so treating the legs as independent inflates the one term that
actually earns.

The both-fill branch carries no drift term, and that is an identity rather than an
omission. If both legs fill, the position is flat and the profit is the spread
regardless of when each leg filled -- see ``accounting.matched_round_trip_cents``.
Drift only bites a leg that stays unmatched.

``drift`` is the **observable** post-fill price move. The unobservable part -- the
adverse-selection cost of a fill that looked benign at decision time -- enters as a
free parameter ``alpha`` charged to unmatched legs only. Roughly half of informed
flow leaves no signature in the price feed before it arrives, so ``alpha`` cannot be
estimated from the tape. It is scanned instead, and the verdict is read off whether
its admissible range has any room left.
"""

from __future__ import annotations


def leg_value_cents(
    edge_cents: float,
    rebate_cents: float,
    drift_cents: float,
    alpha_cents: float = 0.0,
) -> float:
    """Value of a single unmatched filled leg."""
    if alpha_cents < 0.0:
        raise ValueError("alpha is a cost and cannot be negative")
    return edge_cents + rebate_cents - drift_cents - alpha_cents


def joint_fill_probability(fill_a: float, fill_b: float, rho: float) -> float:
    """P(both legs fill), corrected for anticorrelation and clipped to be coherent."""
    if not 0.0 <= fill_a <= 1.0 or not 0.0 <= fill_b <= 1.0:
        raise ValueError("fill probabilities must be in [0, 1]")
    if rho < 0.0:
        raise ValueError("rho cannot be negative")
    return min(fill_a * fill_b * rho, fill_a, fill_b)


def unmatched_weight(fill_a: float, fill_b: float, rho: float) -> float:
    """Expected number of unmatched filled legs -- the coefficient on ``alpha``."""
    p_both = joint_fill_probability(fill_a, fill_b, rho)
    return max(0.0, fill_a - p_both) + max(0.0, fill_b - p_both)


def slot_ev_cents(
    fill_a: float,
    fill_b: float,
    rho: float,
    spread_cents: float,
    rebate_a_cents: float,
    rebate_b_cents: float,
    drift_a_cents: float,
    drift_b_cents: float,
    edge_a_cents: float,
    edge_b_cents: float,
    alpha_cents: float = 0.0,
) -> float:
    """Probability-weighted EV of one quoting decision, in cents."""
    p_both = joint_fill_probability(fill_a, fill_b, rho)
    p_only_a = max(0.0, fill_a - p_both)
    p_only_b = max(0.0, fill_b - p_both)

    both = p_both * (spread_cents + rebate_a_cents + rebate_b_cents)
    only_a = p_only_a * leg_value_cents(edge_a_cents, rebate_a_cents, drift_a_cents, alpha_cents)
    only_b = p_only_b * leg_value_cents(edge_b_cents, rebate_b_cents, drift_b_cents, alpha_cents)
    return both + only_a + only_b


def ev_at_alpha_cents(
    ev_at_zero_cents: float,
    unmatched_weight_value: float,
    alpha_cents: float,
) -> float:
    """``EV(alpha) = EV(0) - unmatched_weight * alpha`` -- linear and decreasing."""
    if alpha_cents < 0.0:
        raise ValueError("alpha is a cost and cannot be negative")
    if unmatched_weight_value < 0.0:
        raise ValueError("unmatched weight cannot be negative")
    return ev_at_zero_cents - unmatched_weight_value * alpha_cents


def breakeven_alpha_cents(
    ev_at_zero_cents: float,
    unmatched_weight_value: float,
) -> float | None:
    """The ``alpha`` at which EV crosses zero, or ``None`` if no such ``alpha`` exists.

    Because ``EV(alpha)`` is decreasing in ``alpha >= 0``:

    * ``EV(0) <= 0`` -> no non-negative adverse cost rescues the policy. The
      rejection holds in the best case the policy is entitled to, which is why a
      negative ``EV(0)`` is a decisive result rather than a pessimistic one.
    * otherwise the policy survives only while the true adverse cost stays below
      the returned threshold.

    This is the decision structure of the whole study: an unmeasurable quantity is
    never guessed, only bounded.
    """
    if unmatched_weight_value <= 0.0:
        return None
    if ev_at_zero_cents <= 0.0:
        return None
    return ev_at_zero_cents / unmatched_weight_value
