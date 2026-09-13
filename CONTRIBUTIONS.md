# Contributions and reading routes

This record connects my historical research questions to inspectable implementations and evidence.
The public package is a curated extraction of a larger research codebase, with explicit corrections
and compact input releases. Publication-only explanatory additions are identified separately.

## Contribution map

| ID | Contribution | Implementation and evidence |
|---|---|---|
| C-PRICING | Constructed and compared feed/anchor/link-function descriptions of binary market prices; estimated a market-implied pricing scale and feature-dependent alternatives | [Derivation](docs/market-pricing-model.md), [estimation procedure](docs/pricing-estimation.md), [pricing code](src/btc5m_research/pricing_estimation.py), [frozen feature study](data/pricing/README.md) |
| C-DATA | Aligned asynchronous feeds and books by information availability; separated cross-venue basis from true price events and recorder gaps from calm markets | [Engineering](docs/data-engineering.md), [microstructure code](src/btc5m_research/microstructure.py), [health masks](src/btc5m_research/clean_index.py) |
| C-RESPONSE | Measured feed-to-book direction, reaction time and confirmation; compared queue depletion proxies with censoring and placebo controls | [Response measurements](docs/market-response.md), [queue mechanics](docs/queue-and-fill-mechanics.md), [aggregate audit](estimators/mechanics_audit.py) |
| C-INVENTORY | Expressed UP/DOWN split inventory as paired collateral plus unmatched settlement exposure, with historical fee and rebate accounting | [EV derivation](docs/mdp-ev-chain.md), [accounting code](src/btc5m_research/accounting.py), [binary risk derivation](docs/binary-risk-and-market-making.md) |
| C-POLICY | Built a joint-fill EV decision model, book-priced action selection and inventory rebalancing; evaluated regime, directional and terminal-handling choices | [Policies and versions](docs/strategies.md), [policy code](src/btc5m_research/policy.py), [EV code](src/btc5m_research/ev_chain.py), [recorded-slot audit](estimators/policy_audit.py) |
| C-VALIDATION | Used fresh chronological blocks, scrambled signals, paired comparisons and execution diagnostics to revise policy conclusions | [Experiment history](docs/negative-results.md), [simulation coverage](docs/simulation-coverage.md), [D12 verifier](estimators/d12_public_verifier.py) |

## Choose a route

**Quantitative research:** start with the pricing derivation and estimation procedure. Follow the
feature table into scale-model comparison, then read the binary-risk derivation and experiment
history. Notice how the target changes between market-implied scale, subsequent feed volatility,
binary outcome probability and policy value.

**Quantitative trading:** start with inventory accounting and the EV chain. Follow the four fill
outcomes into book-based action selection, inventory handling and the paired policy audit. Queue
access, conditional drift, quantity and latency explain why an attractive signal is insufficient
to determine the economics of an order.

**Research engineering:** start with data engineering and the microstructure walkthrough. Inspect
as-of joins, staleness masks, activation timing and queue walks, then follow the frozen-input hashes
and executable rechecks. The package exposes calculation and validation mechanisms rather than
requiring access to a running trading account.

## What is historical, extracted or newly clarified?

- **Historical work:** model investigations, recorder/event methodology, empirical calibration,
  policy versions, replay experiments and execution diagnostics from May-July 2026.
- **Public extraction:** reference components, selected sanitized feature records, aggregate
  mechanics summaries, recorded per-slot simulator outputs and reproducible audit commands.
- **Publication corrections:** feasible joint-fill probabilities, preservation of real zero
  inputs, explicit unknown states, input validation and reconciled source/version descriptions.
  Recomputing archived outputs does not imply those outputs used the corrected reference code.
- **New exposition:** exact Bernoulli CARA indifference calculations in
  [risk.py](src/btc5m_research/risk.py), clarifying the earlier binary-risk argument. This is
  a valuation diagnostic, not a historically deployed Avellaneda-Stoikov strategy.

The implemented policy is a greedy one-step EV selector with inventory rules. The MDP formulation
organizes states, transitions and continuation questions; this repository does not claim a solved
Bellman policy, an identified competitor algorithm or independently established live profitability.

## Grounded application descriptions

These sentences describe the work without turning an experimental score into a trading claim:

- Developed Brownian-probit models of short-horizon binary market prices, including feed/anchor
  diagnostics and market-implied volatility feature studies.
- Built event-driven market-data analysis with causal joins, dropout masks and queue/activation
  modeling; investigated how measurement choices change apparent market-making value.
- Implemented split-inventory accounting and joint-fill EV action selection, and evaluated policy
  variants using paired replay comparisons, chronological blocks and signal placebos.
- Released reproducible research components, archived-feature analyses and recorded-output audits,
  with explicit mappings from equations and assumptions to code and evidence.

When adding numbers, retain the relevant sample, unit, policy version and evaluation status from
the [claim register](evidence/claim_ledger.yaml). The [profile research index](https://github.com/ErenEgeCelik/ErenEgeCelik/blob/main/RESEARCH_INDEX.md)
connects these contributions to the separate weather programme.
