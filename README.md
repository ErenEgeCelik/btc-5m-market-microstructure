# BTC Five-Minute Markets

**Pricing, market microstructure and policy evaluation in historical crypto up/down markets.**

How much of a short-horizon binary market's price can be explained by a simple model? What happens
when that model becomes a market-making policy and must contend with queue position, latency and
adverse selection? This repository collects my research on those questions in Polymarket BTC
five-minute markets during June–July 2026.

The work connects a Brownian-probit pricing model, feed and order-book measurements, split-inventory
accounting and controlled policy experiments. It includes negative results and revisions to earlier
conclusions. It is a historical study under point settlement, not a claim about current profitability.

## Run an example

Python 3.10 or newer; the following commands require no third-party packages or credentials:

```bash
python -B examples/walkthrough.py
python -B estimators/d12_public_verifier.py --check
python -B -m unittest discover -s tests -v
```

The walkthrough uses a small synthetic tape to illustrate single-feed selection, causal reference
lookup and maker activation. The verifier applies the published decision rule to stored aggregate
statistics. Neither command reconstructs the original empirical estimates from raw recordings.

## Findings

- **Pricing structure:** a transformed Brownian-probit model described much of the measured within-slot
  variation in market mids. This concerns the market price, not an identified participant's quotes.
- **Measurement:** merging last ticks from two venues manufactured spike signals; ignoring maker
  activation credited fills before an order could exist. Both affected policy interpretation.
- **Policy evaluation:** the specified static front-quoting candidate was rejected on fresh data even
  with the unobserved benign-fill cost set to zero. Fresh EV(0) was **−0.9845 cents per eligible
  decision moment**, with a 90% slot-cluster interval **[−1.626, −0.364]**, across **312 moments in
  193 slots**. This result is scoped to the tested policy and assumptions.
- **Execution diagnostics:** a replay/paper discrepancy led to investigation of harness and data
  failures. The broken paper run does not establish a clean strategy's economic performance.

## Read the research

Start with the [working paper](paper/manuscript.md), or follow the methods:

1. [Market and historical settlement](docs/market-and-settlement.md)
2. [Market pricing model](docs/market-pricing-model.md)
3. [Inventory accounting and EV decomposition](docs/mdp-ev-chain.md)
4. [Queue and fill mechanics](docs/queue-and-fill-mechanics.md)
5. [Replay and paper coverage](docs/simulation-coverage.md)
6. [Experiments and revisions](docs/negative-results.md)
7. [Evidence and limitations](docs/evidence-and-limitations.md)

| Location | Contents |
|---|---|
| `src/btc5m_research/` | Small reference implementations of pricing, accounting, queue and EV components |
| `examples/` | Synthetic inputs and runnable walkthrough |
| `estimators/` | Deterministic D12 decision-rule verifier |
| `evidence/` | Aggregate result, input hash and claim register |
| `paper/` | Feedback-ready working manuscript and figure provenance |
| `tests/` | Component and verifier checks |

[Reproducibility](REPRODUCIBILITY.md) explains what can be rerun.
[Security and scope](SECURITY.md) describes excluded operational material.

## Author

[Eren Ege Çelik](https://www.erenege.dev), independent quantitative researcher.
Related work: [weather markets](https://github.com/ErenEgeCelik/weather-market-research).
Questions about methods, assumptions and reproducibility are welcome through repository issues.

Code and documentation are available under the [MIT license](LICENSE).
