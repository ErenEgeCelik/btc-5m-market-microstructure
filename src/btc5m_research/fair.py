"""Brownian-probit reference functions under an idealized constant-volatility model.

See docs/ for empirical scope and limitations. These reference components
do not establish profitability or guarantee real-world queue bounds.
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
    bias in the fair value. This heuristic does not guarantee a martingale under changing parameters.
    """
    if base <= 0.0:
        raise ValueError("base sigma must be positive")
    if realized_volatility < 0.0:
        raise ValueError("realized volatility cannot be negative")
    return base + vol_coefficient * realized_volatility


def gap_signal_cents(fair: float, mid: float, baseline: float) -> float:
    """High-pass filtered (fair - mid), in cents.

    The level of ``fair - mid`` carries a slow bias; the deviation of that level
    from its own slow average is the timing signal. This function only computes the signal; its economic value and latency
    sensitivity require a separate empirical evaluation.
    """
    return ((fair - mid) - baseline) * 100.0
