"""Portable historical measurement operations, without recorder or order clients.

Source families and differences are described in the three mechanics documents.
Times are arrival-clock seconds; book values are probabilities; volume is shares.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from math import expm1, isfinite
from typing import Sequence


@dataclass(frozen=True)
class ArrivalSeries:
    times: Sequence[float]
    values: Sequence[float]

    def __post_init__(self) -> None:
        # Freeze mutable caller inputs so validation remains true after construction.
        object.__setattr__(self, "times", tuple(self.times))
        object.__setattr__(self, "values", tuple(self.values))
        if len(self.times) != len(self.values):
            raise ValueError("times and values must have equal length")
        if any(not isfinite(v) for v in (*self.times, *self.values)):
            raise ValueError("series values must be finite")
        if any(b < a for a, b in zip(self.times, self.times[1:])):
            raise ValueError("arrival times must be nondecreasing")

    def index_at(self, time: float, max_age: float) -> int | None:
        if not isfinite(time) or not isfinite(max_age) or max_age < 0:
            raise ValueError("time and age must be finite; age nonnegative")
        index = bisect_right(self.times, time) - 1
        if index < 0 or time - self.times[index] > max_age:
            return None
        return index

    def at(self, time: float, max_age: float) -> float | None:
        index = self.index_at(time, max_age)
        return None if index is None else self.values[index]


def normalize_trade(token: str, taker_side: str, price: float, size: float) -> dict:
    """tape_lib.load UP-space mapping; no duplicate-trade inference is attempted."""
    if token not in {"up", "down"} or taker_side not in {"BUY", "SELL"}:
        raise ValueError("unknown token or taker side")
    if not all(isfinite(v) for v in (price, size)) or not 0 < price < 1 or size < 0:
        raise ValueError("price must be interior and size nonnegative")
    ask = (token == "up" and taker_side == "BUY") or (token == "down" and taker_side == "SELL")
    return {"maker_side": "ask" if ask else "bid",
            "price": price if token == "up" else 1 - price, "size": size}


def first_book_response(book: ArrivalSeries, event_time: float, direction: int,
                        horizon: float = 3.0, max_age: float = 0.5,
                        break_s: float = 1.5) -> dict:
    """D4 first *nonzero* mid move, with structural breaks explicitly separated.

    Input must already represent valid, cent-rounded touch midpoints. Same-time
    records are known at decision time and cannot count as a later response.
    """
    if direction not in (-1, 1) or horizon <= 0 or break_s <= 0:
        raise ValueError("direction must be +/-1 and horizons positive")
    start = book.index_at(event_time, max_age)
    if start is None:
        return {"status": "missing", "latency_s": None}
    for index in range(start + 1, len(book.times)):
        time = book.times[index]
        if time > event_time + horizon:
            break
        if time - book.times[index - 1] > break_s:
            return {"status": "structural_break", "latency_s": None}
        change = book.values[index] - book.values[start]
        if change:
            return {"status": "correct" if change * direction > 0 else "wrong",
                    "latency_s": time - event_time, "signed_move_c": 100 * direction * change}
    return {"status": "fizzle", "latency_s": None}


def calm_before_spike(feed: ArrivalSeries, event_time: float, spike_window: float = 0.2,
                      calm_window: float = 2.0, threshold: float = 3.0,
                      max_age: float = 0.5) -> bool | None:
    """Pre-spike range test; incomplete or stale history returns unknown (None).

    Stronger public guard than the historical vectorized range helper: require an
    observation as-of both window boundaries, and reject gaps exceeding max_age.
    """
    if min(spike_window, calm_window, threshold) <= 0:
        raise ValueError("windows and threshold must be positive")
    end = event_time - spike_window
    first = feed.index_at(end - calm_window, max_age)
    last = feed.index_at(end, max_age)
    if first is None or last is None:
        return None
    times = feed.times[first:last + 1]
    if any(b - a > max_age for a, b in zip(times, times[1:])):
        return None
    values = feed.values[first:last + 1]
    return max(values) - min(values) < threshold


def decompose_depth(before: dict[int, float], after: dict[int, float],
                    trades: dict[int, float]) -> dict[str, float]:
    """D14 price-level decomposition for one maker side and one snapshot interval.

    Prices are integer cents. Trades must match the interval and economic side.
    A disappeared top-five level is treated as removal, which is an identifiability
    limitation if it merely fell outside recorded depth.
    """
    for mapping in (before, after, trades):
        if any(not isfinite(v) or v < 0 for v in mapping.values()):
            raise ValueError("depth and trades must be finite and nonnegative")
    removed = added = traded = 0.0
    for price in before.keys() | after.keys():
        delta = after.get(price, 0.0) - before.get(price, 0.0)
        traded += trades.get(price, 0.0)
        removed += max(0.0, -delta - trades.get(price, 0.0))
        added += max(0.0, delta)
    return {"unexplained_removal": removed, "net_addition": added,
            "trades_at_recorded_levels": traded}


@dataclass(frozen=True)
class FillObservation:
    cap_s: float
    fill_s: float | None
    flow_sh_s: float
    depth_sh: float

    def __post_init__(self) -> None:
        if not all(isfinite(v) for v in (self.cap_s, self.flow_sh_s, self.depth_sh)):
            raise ValueError("capacity, flow and depth must be finite")
        if self.cap_s <= 0 or self.flow_sh_s < 0 or self.depth_sh <= 0:
            raise ValueError("capacity/depth positive; flow nonnegative")
        if self.fill_s is not None and (not isfinite(self.fill_s) or not 0 <= self.fill_s <= self.cap_s):
            raise ValueError("a reported fill must occur within observation capacity")


def empirical_fill_table(observations: Sequence[FillObservation], horizon: float,
                         cuts: Sequence[float] = (0.25, 0.5, 1, 2, 4)) -> list[dict]:
    """D7 cap>=T conditional curves, preserving exact integer denominators."""
    if not isfinite(horizon) or horizon <= 0:
        raise ValueError("horizon must be positive")
    if any(not isfinite(x) or x <= 0 for x in cuts) or list(cuts) != sorted(set(cuts)):
        raise ValueError("cuts must be positive and strictly increasing")
    result = [{"bucket": i, "n": 0, "fills": 0, "x_sum": 0.0} for i in range(len(cuts) + 1)]
    for observation in observations:
        if observation.cap_s < horizon:
            continue
        x = observation.flow_sh_s * horizon / observation.depth_sh
        cell = result[bisect_right(cuts, x)]
        cell["n"] += 1
        cell["fills"] += int(observation.fill_s is not None and observation.fill_s <= horizon)
        cell["x_sum"] += x
    for cell in result:
        cell["p"] = cell["fills"] / cell["n"] if cell["n"] else None
        cell["x_mean"] = cell.pop("x_sum") / cell["n"] if cell["n"] else None
    return result


def fit_exponential_hazard(observations: Sequence[FillObservation]) -> dict:
    """D7 censored-exponential MLE; a model computation, not an endorsement."""
    fills = n = zero_rate = 0
    exposure = 0.0
    for observation in observations:
        if observation.flow_sh_s == 0:
            zero_rate += 1
            continue
        n += 1
        fills += int(observation.fill_s is not None)
        duration = observation.cap_s if observation.fill_s is None else observation.fill_s
        exposure += observation.flow_sh_s / observation.depth_sh * duration
    return {"k": fills / exposure if exposure > 0 else None,
            "events": fills, "rate_weighted_exposure": exposure,
            "positive_rate_n": n, "zero_rate_n": zero_rate}


def hazard_probability(k: float, flow_sh_s: float, depth_sh: float, horizon: float) -> float:
    """Stable arithmetic for 1-exp(-k*lambda*T/r0), including zero flow."""
    if not all(isfinite(v) for v in (k, flow_sh_s, depth_sh, horizon)):
        raise ValueError("hazard inputs must be finite")
    if min(k, flow_sh_s, horizon) < 0 or depth_sh <= 0:
        raise ValueError("depth positive; remaining parameters nonnegative")
    return -expm1(-k * flow_sh_s * horizon / depth_sh)
