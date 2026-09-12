# Synthetic walkthrough

Run `python -B examples/walkthrough.py` from the repository root. The JSONL rows are hand-authored
synthetic timestamps, venue labels and prices. A fixed 49-dollar venue offset illustrates why
alternating last ticks cannot be treated as a single signal stream. This is not recorded market data.

Expected checks: three Binance ticks; causal reference 100001; zero fill before activation; one share
filled after activation behind three shares of modeled queue. The probability is illustrative.
