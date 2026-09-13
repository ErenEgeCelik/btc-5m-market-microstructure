"""Expected value of one modeled paired quoting decision.

For marginal fill probabilities A and B and joint probability J, the four
outcome weights are J, A-J, B-J and 1-A-B+J. The joint model A*B*rho is
projected onto the Frechet bounds max(0,A+B-1) <= J <= min(A,B).
Only unmatched branches incur the additional alpha cost. These probabilities
are modeling inputs, not evidence of actual queue rank or independence.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class FillBranches:
    """A normalized partition, not four independent events."""

    both: float
    only_a: float
    only_b: float
    neither: float


def fill_branches(fill_a: float, fill_b: float, rho: float) -> FillBranches:
    """Joint/marginal-consistent outcomes for one equal-quantity paired quote."""
    joint = joint_fill_probability(fill_a, fill_b, rho)
    return FillBranches(joint, fill_a - joint, fill_b - joint,
                        max(0.0, 1.0 - fill_a - fill_b + joint))


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
    """P(both legs fill), projected onto both Frechet bounds."""
    if not 0.0 <= fill_a <= 1.0 or not 0.0 <= fill_b <= 1.0:
        raise ValueError("fill probabilities must be in [0, 1]")
    if not isfinite(rho) or rho < 0.0:
        raise ValueError("rho must be finite and non-negative")
    return max(0.0, fill_a + fill_b - 1.0, min(fill_a * fill_b * rho, fill_a, fill_b))


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
    branches = fill_branches(fill_a, fill_b, rho)
    p_both, p_only_a, p_only_b = branches.both, branches.only_a, branches.only_b

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
