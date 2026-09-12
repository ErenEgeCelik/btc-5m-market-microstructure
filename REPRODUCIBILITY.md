# What can be reproduced here, and what cannot

This repository separates two layers on purpose, and is explicit about which one a reader is
standing on.

## Layer 1 — the verdict layer (fully reproducible here)

```bash
python -B estimators/d12_public_verifier.py          # recompute and write the verdict
python -B estimators/d12_public_verifier.py --check  # recompute and compare, no writes
```

Requirements: Python 3.10 or newer. No third-party packages, no network access, no private data.

The verifier reads `evidence/links_d12.json`, applies the pre-declared decision rule, and emits
`evidence/d12_public_verdict.json` as canonical JSON (sorted keys, two-space indent). `--check`
recomputes and byte-compares instead of writing, so a stale committed verdict fails loudly.

The verdict records the SHA-256 of its input:

```
f8e3959c7c45edd1d5a5f7b2ebe5e17dbce60db653d446413403c61f9a9d2eb7
```

This is the hash of the byte-identical estimator output in the private research repository. It is
the integrity link between the two layers: the aggregate numbers published here are the same bytes
the private estimator produced, and any edit to them changes the hash and fails the check.

## Layer 2 — the event level (not reproducible here)

`evidence/links_d12.json` was produced by an event-level estimator over roughly 19 GB of recorded
order-book, trade, and price-feed data, masked by a dropout index. That estimator and those
recordings are not published: the recordings are large, venue-sourced, and account-adjacent.

So the honest statement is:

- The **decision rule and its application** to the aggregate statistics are independently checkable.
- The **aggregate statistics themselves** are author-attested. A reader who doubts them cannot
  re-derive them from this repository.

`src/btc5m_research/` exists to make the *modelling* independently inspectable even though the
estimation is not: the fair-value map, quote schedule, queue walk, EV rollup, dropout masking, and
fee/rebate accounting are implemented as pure functions with tests and a synthetic fixture. A reader
can confirm the model does what the documentation claims, on data they generate themselves.

## Determinism

- No randomness in the verifier.
- Bootstrap intervals quoted in the evidence were computed with a fixed seed in the private
  estimator; the interval is reported, not recomputed here.
- `examples/synthetic_tape.jsonl` is generated from a fixed seed and contains no market data.

## Environment actually used

Python 3.11 on Windows. The verifier and tests use only the standard library, so any Python 3.10+
on any platform should produce identical bytes. If it does not, that is a bug worth an issue.
