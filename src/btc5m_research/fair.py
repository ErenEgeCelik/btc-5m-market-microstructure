"""Brownian-probit fair value and its price-space volatility.

The contract pays $1 if the reference price finishes above the strike. Under a
driftless diffusion for the underlying, the fair probability is the normal CDF of
the standardized distance to the strike:

    P = Phi((F + offset - K) / (sigma * sqrt(tau)))

``F`` is a fast external price feed, ``K`` the strike the venue resolves against,
``offset`` a slow estimate of the level difference between feed and oracle, and
``tau`` the time remaining.

Two consequences shape every downstream decision, and both are derived in
``docs/mdp-ev-chain.md``:

1. Applying Ito to ``P`` removes the drift term identically, so ``P`` is a
   martingale: the expected future fair value is today's. Directional exposure
   therefore has zero expectation by construction, and trading income has to come
   from the spread and the rebate instead.
2. The induced volatility of the *price* depends only on the price and the clock:
   ``sigma_P(P, tau) = phi(Phi^-1(P)) / sqrt(tau)``. It is maximal at ``P = 0.5``,
   vanishes at the rails, and diverges as ``tau -> 0`` for an interior price --
   which is why carrying inventory into settlement is a lottery rather than a
   position.

The martingale property holds only while the volatility used to price is close to
the volatility that realizes. A mis-scaled ``sigma`` injects an apparent drift.
"""

from __future__ import annotations

import math
from statistics import NormalDist

_N = NormalDist()

SQRT_2PI = math.sqrt(2.0 * math.pi)


def norm_cdf(x: float) -> float:
    return _N.cdf(x)


def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def norm_ppf(p: float) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError(f"probability must be in (0, 1), got {p!r}")
    return _N.inv_cdf(p)


def fair_probability(feed: float, strike: float, sigma: float, tau: float, offset: float = 0.0) -> float:
    """P(settle above strike) for a driftless underlying."""
    if sigma <= 0.0:
        raise ValueError("sigma must be positive")
    if tau <= 0.0:
        raise ValueError("tau must be positive; the terminal case is degenerate")
    return norm_cdf((feed + offset - strike) / (sigma * math.sqrt(tau)))


def price_volatility(p: float, tau: float) -> float:
    """sigma_P(P, tau) = phi(Phi^-1(P)) / sqrt(tau), the diffusion of the price itself."""
    if tau <= 0.0:
        raise ValueError("tau must be positive")
    return norm_pdf(norm_ppf(p)) / math.sqrt(tau)


def dynamic_sigma(base: float, vol_coefficient: float, realized_volatility: float) -> float:
    """Volatility used for pricing: a floor plus a term in trailing realized volatility.

    A constant sigma was measured to sit above the market in calm periods and below
    it in volatile ones, which shows up as a fake mean-reverting or trend-following
    bias in the fair value. Keeping sigma responsive is what keeps the martingale
    property approximately true.
    """
    if base <= 0.0:
        raise ValueError("base sigma must be positive")
    if realized_volatility < 0.0:
        raise ValueError("realized volatility cannot be negative")
    return base + vol_coefficient * realized_volatility


def gap_signal_cents(fair: float, mid: float, baseline: float) -> float:
    """High-pass filtered (fair - mid), in cents.

    The level of ``fair - mid`` carries a slow bias; the deviation of that level
    from its own slow average is the timing signal. Being a level rather than a
    velocity, it degrades gracefully under latency -- a measured ~12% loss at
    250 ms -- where contemporaneous order-flow signals collapse.
    """
    return ((fair - mid) - baseline) * 100.0
