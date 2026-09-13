"""Binary terminal-risk diagnostics, derived for this publication.

These are frozen-inventory valuations, not the historical bot's quoting policy.
All payoffs and prices are in dollars for a contract paying one dollar.
"""

from __future__ import annotations

import math


def _inputs(p: float, inventory: float, gamma: float = 0.0) -> None:
    if not all(math.isfinite(x) for x in (p, inventory, gamma)):
        raise ValueError("probability, inventory and risk aversion must be finite")
    if not 0.0 <= p <= 1.0 or gamma < 0.0:
        raise ValueError("probability must be in [0, 1] and gamma nonnegative")
    if not math.isfinite(gamma * inventory):
        raise ValueError("gamma times inventory must be finite")


def terminal_moments(p: float, up: float, down: float) -> tuple[float, float]:
    """Mean dollars and variance dollars squared of up*X + down*(1-X)."""
    _inputs(p, up)
    _inputs(p, down)
    if p == 0.0:
        return down, 0.0
    if p == 1.0:
        return up, 0.0
    imbalance = up - down
    mean = p * up + (1.0 - p) * down
    variance = imbalance * imbalance * p * (1.0 - p)
    if not math.isfinite(mean) or not math.isfinite(variance):
        raise ValueError("terminal moments exceed finite floating-point range")
    return mean, variance


def _log_bernoulli_mgf(p: float, z: float) -> float:
    """log E[exp(z*X)], retaining precision near z=0 and avoiding exp overflow."""
    if p == 0.0:
        return 0.0
    if p == 1.0:
        return z
    if abs(z) < 0.5:
        return math.log1p(p * math.expm1(z))
    a, b = math.log1p(-p), math.log(p) + z
    hi, lo = max(a, b), min(a, b)
    return hi + math.log1p(math.exp(lo - hi))


def _softplus(z: float) -> float:
    return max(z, 0.0) + math.log1p(math.exp(-abs(z)))


def _logadd(a: float, b: float) -> float:
    return max(a, b) + math.log1p(math.exp(-abs(a - b)))


def certainty_equivalent(p: float, inventory: float, gamma: float) -> float:
    """CARA certainty equivalent of inventory*X; gamma has units 1/dollar."""
    _inputs(p, inventory, gamma)
    if gamma == 0.0:
        return inventory * p
    return -_log_bernoulli_mgf(p, -gamma * inventory) / gamma


def reservation_prices(p: float, inventory: float, gamma: float) -> tuple[float, float]:
    """Exact one-share (bid, ask) indifference values for frozen binary inventory.

    Reweighting the Bernoulli law avoids subtracting two large certainty equivalents.
    No arrival intensity, queue model, latency or optimal control is represented.
    """
    _inputs(p, inventory, gamma)
    if gamma == 0.0 or p in (0.0, 1.0):
        return p, p
    log_odds = math.log(p) - math.log1p(-p) - gamma * inventory
    if gamma >= 0.5:
        # Keep both log-weights: rounding a tilted probability to zero or one
        # can erase mass that a large one-share utility increment recovers.
        log_p = -_softplus(-log_odds)
        log_complement = -_softplus(log_odds)
        return (-_logadd(log_complement, log_p - gamma) / gamma,
                _logadd(log_complement, log_p + gamma) / gamma)
    if log_odds >= 0.0:
        tilted_p = 1.0 / (1.0 + math.exp(-log_odds))
    else:
        e = math.exp(log_odds)
        tilted_p = e / (1.0 + e)
    return (
        -_log_bernoulli_mgf(tilted_p, -gamma) / gamma,
        _log_bernoulli_mgf(tilted_p, gamma) / gamma,
    )
