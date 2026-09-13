"""Book-priced, one-step D15 policy extraction. No orders or fill simulation.

Historical inputs: d8_unified.py EVM decision branch and links_d12_calib.json.
Public corrections: Fréchet-consistent joints, explicit unknown state, zero-safe
parameter lookup, finite/valid input checks. Archived results are not reruns of
this corrected implementation. Prices/EV/drift use cents; quantity uses shares.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from math import isfinite
from typing import Mapping

from .ev_chain import slot_ev_cents

REGIMES = ("R0", "R+", "R-", "NEUT")
SCRAMBLED = {"R0": "R+", "R+": "R0", "R-": "NEUT", "NEUT": "R-"}


@dataclass(frozen=True)
class DecisionState:
    """A=Up ask / sell Up; B=synthetic Up bid / sell Down from a split pair."""

    bid_cents: float
    ask_cents: float
    ask_visible_shares: float
    bid_visible_shares: float
    ask_flow_shares_per_second: float
    bid_flow_shares_per_second: float
    net_up_shares: float
    elapsed_seconds: float
    regime: str | None

    def __post_init__(self):
        numeric = [value for name, value in vars(self).items() if name != "regime"]
        if not all(isfinite(value) for value in numeric):
            raise ValueError("state values must be finite")
        if not 0 < self.bid_cents < self.ask_cents < 100:
            raise ValueError("book must satisfy 0 < bid < ask < 100 cents")
        if min(self.ask_visible_shares, self.bid_visible_shares,
               self.ask_flow_shares_per_second, self.bid_flow_shares_per_second) < 0:
            raise ValueError("size and flow cannot be negative")
        if self.regime is not None and self.regime not in REGIMES:
            raise ValueError("unknown regime label")


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    ask_up_cents: float
    bid_up_cents: float
    ask_quantity_shares: float
    bid_quantity_shares: float
    unit_ev_cents: dict[str, float]
    reason: str


def regime_from_move(move_dollars: float | None) -> str | None:
    """Classify a validated as-of 1.5-second single-venue move; None stays unknown."""
    if move_dollars is None or not isfinite(move_dollars):
        return None
    if abs(move_dollars) < 3:
        return "R0"
    if abs(move_dollars) >= 8:
        return "R+" if move_dollars > 0 else "R-"
    return "NEUT"


def fill_lookup(calibration: Mapping, side: str, flow: float, wall: float) -> float:
    """Historical empirical x=flow*10s/wall lookup; not the rejected exponential fit."""
    if side not in ("A", "B"):
        raise ValueError("side must be A or B")
    if not isfinite(flow) or not isfinite(wall) or min(flow, wall) < 0:
        raise ValueError("wall and flow must be finite and non-negative")
    if wall == 0:
        return 0.0  # Historical JOIN convention; front has a separate probability.
    x = flow * calibration["h"] / wall
    label = calibration["xb_lab"][bisect_right(calibration["xb"], x)]
    p = calibration["tables"][side][label]["p"]
    return 0.0 if p is None else float(p)


def choose_action(state: DecisionState, calibration: Mapping, *,
                  scrambled: bool = False, clip_shares: float = 5.0,
                  rebalance_threshold_shares: float = 5.0,
                  inventory_clamp_shares: float = 15.0) -> PolicyDecision:
    """Choose none/A/B/both, with a mandatory reducing side beyond the REB threshold.

    One-step branch EV only. REB overrides the EV filter; unequal REB quantities
    are not assigned a fictitious full-position EV by this per-unit model.
    """
    if not all(isfinite(v) and v > 0 for v in
               (clip_shares, rebalance_threshold_shares, inventory_clamp_shares)):
        raise ValueError("quantity controls must be finite and positive")
    improve = state.ask_cents - state.bid_cents >= 3.0
    ask = state.ask_cents - (1.0 if improve else 0.0)
    bid = state.bid_cents + (1.0 if improve else 0.0)
    def result(action, qa=0.0, qb=0.0, ev=None, reason=""):
        return PolicyDecision(action, ask, bid, qa, qb, ev or {}, reason)
    if state.elapsed_seconds >= 200:
        return result("flatten", reason="Historical terminal risk boundary; no new maker quote.")
    if state.elapsed_seconds < 10:
        return result("none", reason="Outside the historical decision window.")
    if state.regime is None:
        return result("none", reason="Unknown feed state; public guard, not historical NEUT fallback.")
    regime = SCRAMBLED[state.regime] if scrambled else state.regime
    if improve:
        a = calibration["front_pfill"]["A"]
        b = calibration["front_pfill"]["B"]
    else:
        a = fill_lookup(calibration, "A", state.ask_flow_shares_per_second,
                        state.ask_visible_shares)
        b = fill_lookup(calibration, "B", state.bid_flow_shares_per_second,
                        state.bid_visible_shares)
    da = calibration["delta"]["ask"][regime]
    db = calibration["delta"]["bid"][regime]
    if not all(isfinite(value) for value in (a, b, da, db, calibration["rho"])):
        raise ValueError("selected calibration values must be finite")
    mid = (state.bid_cents + state.ask_cents) / 2.0
    edge_a, edge_b = ask - mid, mid - bid
    # Historical maker rebate = 1.4 p(1-p) cents/share, at each executed price.
    ra, rb = 1.4 * (ask / 100) * (1 - ask / 100), 1.4 * (bid / 100) * (1 - bid / 100)
    ev = {"none": 0.0, "A": a * (edge_a + ra - da),
          "B": b * (edge_b + rb - db)}
    ev["both"] = slot_ev_cents(a, b, calibration["rho"], ask - bid,
                              ra, rb, da, db, edge_a, edge_b)
    net = state.net_up_shares
    open_a, open_b = net > -inventory_clamp_shares, net < inventory_clamp_shares
    if net >= rebalance_threshold_shares:
        qa, qb = net, clip_shares if open_b and ev["B"] > 0 else 0.0
        return result("both" if qb else "A", qa, qb, ev, "Mandatory reducing ask; optional positive-EV bid.")
    if net <= -rebalance_threshold_shares:
        qa, qb = clip_shares if open_a and ev["A"] > 0 else 0.0, -net
        return result("both" if qa else "B", qa, qb, ev, "Mandatory reducing bid; optional positive-EV ask.")
    candidates = ["none"]
    if open_a: candidates.append("A")
    if open_b: candidates.append("B")
    if open_a and open_b: candidates.append("both")
    action = max(candidates, key=ev.__getitem__)
    return result(action, clip_shares if action in ("A", "both") else 0.0,
                  clip_shares if action in ("B", "both") else 0.0, ev,
                  "Highest positive one-step EV; equal-score ties retain earlier candidate.")


def adverse_side(move_direction: int) -> str:
    """An upward underlying move threatens the resting Up ask; downward threatens B."""
    if move_direction not in (-1, 1):
        raise ValueError("direction must be -1 or +1")
    return "A" if move_direction > 0 else "B"


def fill_precedes_cancel(fill_seconds: float, decision_seconds: float,
                         trigger_seconds: float | None, window_end_seconds: float,
                         post_seconds: float = 0.05, cancel_seconds: float = 0.05) -> bool:
    """Historical timestamp eligibility only; this is not proof that an order filled.

    Equal fill/cancel timestamps favor fill, preserving the conservative historical
    comparison. No print before activation can be credited.
    """
    values = [fill_seconds, decision_seconds, window_end_seconds, post_seconds, cancel_seconds]
    if trigger_seconds is not None: values.append(trigger_seconds)
    if not all(isfinite(value) for value in values) or min(post_seconds, cancel_seconds) < 0:
        raise ValueError("timestamps must be finite; latencies non-negative")
    cutoff = window_end_seconds if trigger_seconds is None else min(
        window_end_seconds, trigger_seconds + cancel_seconds)
    return decision_seconds + post_seconds <= fill_seconds <= cutoff
