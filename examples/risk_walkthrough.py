"""Frozen-inventory binary valuation: an explanatory derivation, not a quote engine."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from btc5m_research.fair import price_volatility
from btc5m_research.risk import reservation_prices, terminal_moments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    rows = []
    for q in (-10, 0, 10):
        bid, ask = reservation_prices(0.5, q, 0.1)
        rows.append({'net_shares': q, 'indifference_bid_dollars': bid, 'indifference_ask_dollars': ask})
    report = {
        'scope': 'Publication derivation with synthetic inputs; no order policy or measured returns.',
        'paired_8_up_8_down_mean_variance': terminal_moments(0.5, 8, 8),
        'unbalanced_12_up_8_down_mean_variance': terminal_moments(0.5, 12, 8),
        'binary_diffusion_at_p_half': {str(tau): price_volatility(0.5, tau) for tau in (100, 1)},
        'gamma_per_dollar': 0.1, 'probability': 0.5, 'inventory_valuations': rows,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(report['scope'])
        print('8 UP + 8 DOWN: terminal payoff $8 with zero settlement variance.')
        print('12 UP + 8 DOWN, p=0.5: expected payoff $10, variance 4 dollars squared.')
        print('At fixed p=0.5, instantaneous price diffusion rises 10x from tau=100s to 1s.')
        for row in rows:
            print(f"net={row['net_shares']:+3d}: CARA bid={row['indifference_bid_dollars']:.4f}, ask={row['indifference_ask_dollars']:.4f}")


if __name__ == '__main__':
    main()
