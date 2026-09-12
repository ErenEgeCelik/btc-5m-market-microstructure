# BTC 5-Minute Market Microstructure

**A verifier-first study of one market-making policy, and the measurement that rejected it.**

This repository documents how an intuitive market-making idea for Polymarket's BTC 5-minute binary
contracts was turned into an explicit expected-value system, tested against the venue's real
settlement, feed, and order-book mechanics, and then **rejected** at the only queue position the
strategy could actually reach.

It ships the deterministic verifier for the decisive result, the aggregate evidence it runs on, and
the reasoning that makes the rejection believable. It does **not** ship a trading bot.

---

## The verdict, up front

```
claim:    Static "improve-inside-calm-front" quoting retains positive expected value
          after 50 ms maker activation, on fresh chronological out-of-sample data.

decision: DEAD

fresh out-of-sample EV(0)  = -0.98 cents per eligible decision moment
90% slot-cluster interval  = [-1.63, -0.36]        (entirely below zero)
sample                     = 312 eligible moments / 193 slots
discovery blocks           = +0.34 and +0.43       (this is why it looked real)
chronological split        = first 70% +0.38  ->  last 30% -1.00
worst-slot removed         = still negative
```

`EV(0)` fixes the one quantity the recorded data cannot observe — the adverse-selection cost of a
fill that looked benign — at **zero**, its most favourable possible value. `EV(α)` is decreasing in
`α ≥ 0`, so a negative `EV(0)` rejects every non-negative assumption about that unknown at once.
The policy is not rejected because a pessimistic parameter was chosen; it is rejected **in the
best case it is entitled to**.

Reproduce it:

```bash
python -B estimators/d12_public_verifier.py --check
```

The verifier recomputes the verdict from `evidence/links_d12.json`, compares it byte-for-byte with
the committed `evidence/d12_public_verdict.json`, and records the SHA-256 of its input so a later
change to the evidence cannot silently change the conclusion.

---

## Why a negative result is the product

Three things make this worth publishing rather than deleting.

**1. The positive version existed first.** On the discovery blocks the same policy measured
`+0.34` and `+0.43` cents per moment. A chronological split and a fresh block turned it negative.
The repository shows both, in order, so the reader can see exactly what a convincing-but-wrong
result looks like before it dies.

**2. Two independent errors had to be removed before the number meant anything.** A merged
two-exchange price feed manufactured spike signals that a matched placebo exposed (a persistent
inter-venue level offset makes the merged series saw-tooth). And counting fills from the decision
instant rather than from maker order activation credited prints that no order could have captured —
roughly two-thirds of the apparent front-quoting edge was this latency illusion. Both corrections
are in the methodology, not hidden in a changelog.

**3. A replay that agrees with itself can still disagree with reality.** The same engine was run
over the recorded tape of a window in which a paper engine had already traded. On six slots where
the paper engine lost about `$31`, the replay credited about `+$21`. In calm conditions the two
reconciled to roughly 30%. That gap is the repository's strongest methodological result and the
reason every positive replay number here is labelled an upper bound.

---

## What is in here

| Path | Contents |
|---|---|
| `estimators/d12_public_verifier.py` | Deterministic verdict reproducer, standard library only |
| `evidence/links_d12.json` | Aggregate estimator output the verdict is computed from |
| `evidence/d12_public_verdict.json` | Committed verdict, regenerated and checked by the verifier |
| `evidence/claim_ledger.yaml` | Every external claim with its status, coverage and allowed wording |
| `docs/` | Instrument and settlement, incumbent quote model, EV chain, queue mechanics, simulation coverage, negative results, limitations |
| `src/btc5m_research/` | Sanitized reference implementations of the model pieces the docs describe |
| `tests/` | Accounting invariants, no-lookahead, single-feed signal, dropout masking, queue denominators, verdict reproduction |
| `examples/synthetic_tape.jsonl` | Synthetic fixture so the code paths run without private data |

## What is deliberately not in here

No credentials, keys, wallet or account identifiers, order IDs, or raw account-linked logs. No
deployment topology, host addresses, or remote-control surfaces. No order-submission path, no
cancel-all behaviour, no live or paper trading engine. No raw recorded tapes.

The event-level estimator that produced `links_d12.json` runs against roughly 19 GB of private
recordings and a dropout mask; it is not part of this repository. What is published is the
**verdict layer**: the aggregate statistics, the decision rule applied to them, and an integrity
hash linking the two. `docs/evidence-and-limitations.md` states plainly which claims therefore
remain author-attested rather than independently reproducible here.

---

## Scope, and what this is not evidence for

This studies **one instrument family, one policy family, one queue position, in one measured
period.** It is not a claim that market making is impossible, that the venue is inefficient, or
that the author operated a profitable strategy. No live profitability is claimed anywhere in this
repository.

Two scope limits matter for anyone trying to reuse the result:

- **Queue position.** The rejection applies to the seat the strategy could reach — joining behind
  existing depth, or improving one tick inside a wide spread. It says nothing about the economics
  available to a participant who sets the price level, and the data contain no order identifiers,
  so queue rank is inferred from visible size rather than observed.
- **Settlement regime.** The contracts studied here resolved against a single oracle observation at
  a window boundary. Short-horizon crypto prediction contracts have since moved toward settlement
  on an **average of the final seconds** of a reference index — Kalshi's crypto contracts, for
  example, settle on a 60-second average of the CF Benchmarks real-time index. Averaged settlement
  changes the terminal payoff from a digital on a point observation to a digital on a partially
  realized average, which changes the endgame variance structure qualitatively. Results measured
  under point settlement should not be carried across that change without re-derivation.

---

## Reading order

1. `docs/market-and-settlement.md` — the instrument, the resolution path, the fee and rebate identities
2. `docs/incumbent-maker-model.md` — reproducing the dominant maker's quote schedule, and why that is understanding rather than edge
3. `docs/mdp-ev-chain.md` — turning the policy into an explicit EV decomposition
4. `docs/queue-and-fill-mechanics.md` — queue access, fill measurement, and what the denominators mean
5. `docs/simulation-coverage.md` — what a replay can and cannot represent, with the same-window comparison
6. `docs/negative-results.md` — the graveyard, in order, with the mechanism that killed each entry
7. `docs/evidence-and-limitations.md` — claim-by-claim coverage and the open unknowns

`REPRODUCIBILITY.md` describes what can be rerun here and what cannot. `SECURITY.md` describes the
sanitization boundary.

## License

Code and documentation: MIT (see `LICENSE`). The aggregate evidence files are published for
verification of the stated claims.
