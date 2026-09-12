"""Historical fee/rebate assumptions and complementary-payoff identities.

Fee coefficients describe the study model, not a current venue schedule or a
guarantee that modeled rebates are earned. Functions return cents unless named
otherwise; p is a probability in (0,1).
"""

from __future__ import annotations

TAKER_FEE_COEFF_CENTS = 7.0
"""Taker fee coefficient: fee = 7 * p * (1 - p) cents per share."""

MAKER_REBATE_FRACTION = 0.20
"""Historical model rebate fraction: 20% of the modeled taker-fee schedule."""

MAKER_REBATE_COEFF_CENTS = TAKER_FEE_COEFF_CENTS * MAKER_REBATE_FRACTION
"""Maker rebate coefficient: rebate = 1.4 * p * (1 - p) cents per share."""


def _check_price(p: float) -> None:
    if not 0.0 < p < 1.0:
        raise ValueError(f"price must be in (0, 1), got {p!r}")


def taker_fee_cents(p: float, size: float = 1.0) -> float:
    """Fee paid when crossing the spread."""
    _check_price(p)
    return TAKER_FEE_COEFF_CENTS * p * (1.0 - p) * size


def maker_rebate_cents(p: float, size: float = 1.0) -> float:
    """Rebate received on a resting fill. Income, not a cost."""
    _check_price(p)
    return MAKER_REBATE_COEFF_CENTS * p * (1.0 - p) * size


def maker_fee_cents(p: float, size: float = 1.0) -> float:
    """Maker fee is zero in the historical study model."""
    _check_price(p)
    return 0.0


def pair_settlement_value_dollars(size: float = 1.0) -> float:
    """A matched YES+NO pair settles at exactly $1 per unit, whatever the outcome.

    This is the invariant the whole strategy is built on: holding both halves is
    direction-free, so a filled pair has no resolution risk.
    """
    return 1.0 * size


def matched_round_trip_cents(
    sell_price_yes: float,
    sell_price_no: float,
    size: float = 1.0,
) -> float:
    """Profit when both legs of a split pair are sold as resting orders.

    Selling both halves returns ``sell_price_yes + sell_price_no`` against a pair
    worth exactly $1, so the trading profit is the spread between them, plus the
    rebate on each filled leg. The result is **path independent** -- the order and
    timing of the two fills do not enter.
    """
    _check_price(sell_price_yes)
    _check_price(sell_price_no)
    spread_cents = (sell_price_yes + sell_price_no - 1.0) * 100.0 * size
    rebates = maker_rebate_cents(sell_price_yes, size) + maker_rebate_cents(sell_price_no, size)
    return spread_cents + rebates
