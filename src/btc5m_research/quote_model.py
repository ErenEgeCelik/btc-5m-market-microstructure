"""Market-mid pricing structure and single-feed reference helpers.

See docs/ for empirical scope and limitations. These reference components
do not establish profitability or guarantee real-world queue bounds.
"""

from __future__ import annotations

import math
from statistics import NormalDist

_N = NormalDist()


def single_feed_series(
    ticks: list[tuple[float, str, float]],
    venue: str,
) -> list[tuple[float, float]]:
    """Project a multi-venue tick stream onto one venue.

    ``ticks`` are ``(timestamp, venue, price)``. Signal construction must run on the
    output of this function, never on a merged last-value series.
    """
    return [(timestamp, price) for timestamp, tick_venue, price in ticks if tick_venue == venue]


def merged_last_value_series(
    ticks: list[tuple[float, str, float]],
) -> list[tuple[float, float]]:
    """The artefact, implemented so that a test can demonstrate it.

    Takes the most recent price regardless of venue. With a persistent inter-venue
    level offset this manufactures alternating jumps that look like spikes.
    """
    return [(timestamp, price) for timestamp, _venue, price in ticks]


def transformed_quote_target(mid: float, tau_s: float) -> float:
    """Transform a market mid into the linear Brownian-probit model space.

    ``Phi^-1(mid) * sqrt(tau)`` is linear in the displacement of the reference price
    from the strike, so a per-slot regression describes this market-price relationship.
    """
    if not math.isfinite(mid) or not 0.0 < mid < 1.0:
        raise ValueError("mid must be a probability in (0, 1)")
    if not math.isfinite(tau_s) or tau_s <= 0.0:
        raise ValueError("tau must be positive")
    return _N.inv_cdf(mid) * math.sqrt(tau_s)


def predicted_mid(reference_displacement: float, sigma: float, tau_s: float) -> float:
    """Invert the schedule back into a price."""
    if not math.isfinite(reference_displacement):
        raise ValueError("reference displacement must be finite")
    if not math.isfinite(sigma) or sigma <= 0.0:
        raise ValueError("sigma must be positive")
    if not math.isfinite(tau_s) or tau_s <= 0.0:
        raise ValueError("tau must be positive")
    return _N.cdf(reference_displacement / (sigma * math.sqrt(tau_s)))


def lagged_reference(
    series: list[tuple[float, float]],
    now: float,
    lag_s: float,
) -> float | None:
    """As-of lookup of the reference price ``lag_s`` before ``now``.

    Strictly causal: it never reads a tick stamped later than ``now - lag_s``, which
    is what the no-lookahead test pins down.
    """
    if not math.isfinite(now) or not math.isfinite(lag_s) or lag_s < 0.0:
        raise ValueError("now must be finite and lag finite/nonnegative")
    if any(not math.isfinite(t) or not math.isfinite(p) for t, p in series):
        raise ValueError("reference ticks must be finite")
    if any(a[0] > b[0] for a, b in zip(series, series[1:])):
        raise ValueError("reference ticks must be time-sorted")
    cutoff = now - lag_s
    value: float | None = None
    for timestamp, price in series:
        if timestamp <= cutoff:
            value = price
        else:
            break
    return value


def synchronized_reference(
    series_by_venue: dict[str, list[tuple[float, float]]],
    now: float,
    lag_s: float = 0.0,
    max_age_s: float = 3.0,
) -> float | None:
    """As-of mean of every explicitly supplied venue, or None when any is unavailable.

    Timestamp and age checks apply at now-lag. This publication helper refuses to
    silently change venue membership when a source goes stale. The historical
    explanatory mean and later Binance-only event signals remain distinct series.
    """
    if not series_by_venue:
        raise ValueError("at least one venue is required")
    if not math.isfinite(max_age_s) or max_age_s < 0:
        raise ValueError("maximum age must be finite and nonnegative")
    values = []
    for series in series_by_venue.values():
        value = lagged_reference(series, now, lag_s)
        if value is None:
            return None
        cutoff = now - lag_s
        last_time = next(t for t, _ in reversed(series) if t <= cutoff)
        if cutoff - last_time > max_age_s:
            return None
        values.append(value)
    return math.fsum(values) / len(values)


def range_scale(range_usd: float, intercept: float = 2.10, slope: float = 0.052) -> float:
    """Historical range-rule arithmetic; the caller must identify its feed and window.

    The defaults reproduce the June refinement, not a newly calibrated scale.
    Within-slot range and pre-slot range have different information sets.
    """
    if not all(math.isfinite(x) for x in (range_usd, intercept, slope)) or range_usd < 0:
        raise ValueError("parameters must be finite and range nonnegative")
    sigma = intercept + slope * range_usd
    if sigma <= 0:
        raise ValueError("range rule must produce a positive scale")
    return sigma


def time_ema(previous: float, observed: float, elapsed_s: float, time_constant_s: float) -> float:
    """One constant-memory elapsed-time EMA update used by the hybrid level/gap design.

    Time-based weight avoids changing the decay rate when feed event frequency changes.
    Inputs must already be aligned causally; this arithmetic helper performs no feed access.
    """
    if not all(math.isfinite(x) for x in (previous, observed, elapsed_s, time_constant_s)):
        raise ValueError("EMA inputs must be finite")
    if elapsed_s < 0 or time_constant_s <= 0:
        raise ValueError("elapsed time must be nonnegative and time constant positive")
    weight = -math.expm1(-elapsed_s / time_constant_s)
    return previous + weight * (observed - previous)


def hybrid_probability(feed: float, offset: float, strike: float, sigma: float, tau_s: float) -> float:
    """Hybrid fair level: fast feed + smoothed oracle/feed basis - settlement strike."""
    return predicted_mid(feed + offset - strike, sigma, tau_s)
