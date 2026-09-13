# Runnable research examples

Run each script from the repository root. See [Reproducibility](../REPRODUCIBILITY.md) for
requirements, audits and the distinction between recorded and synthetic inputs.

| Entry point | Question and input |
|---|---|
| `walkthrough.py` | Causal feed selection and maker activation on hand-authored timestamps; a synthetic $49 venue basis illustrates false merged-feed jumps |
| `pricing_walkthrough.py` | Synthetic transformed-schedule recovery and scale-model comparison on 358 archived feature rows |
| `risk_walkthrough.py` | Binary terminal risk and exact frozen-inventory indifference values on synthetic positions |
| `microstructure_walkthrough.py` | Arrival clocks, feed/book validity, activation and queue assumptions |
| `policy_walkthrough.py` | Book-priced one-step decisions from archived calibration and declared synthetic states |

The original tape demonstration retains its checks: three Binance ticks, causal reference 100001,
zero fill before activation and one share filled after activation behind three modeled queue shares.
It contains no recorded market data. The pricing and policy data guides describe the selected real
research records; none of these examples submits orders or reports realized trading returns.
