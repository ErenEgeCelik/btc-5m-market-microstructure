# Sanitization boundary

This repository is an extract of a private research codebase. The extraction rule was: publish the
**research mechanism**, never the operational surface.

## Never present in this repository

- Credentials, API keys, private keys, environment files
- Wallet addresses, account identifiers, balances
- Order identifiers, fill journals, raw account-linked logs
- Host addresses, usernames, deployment topology, remote-control surfaces
- Order-submission or cancellation code paths
- Raw recorded market tapes

## Why the trading path is absent, not merely disabled

The private engine places real orders. A public copy with submission "commented out" is an
invitation to re-enable it and a liability if someone does. The published code therefore contains
**no venue client at all** — the modelling pieces take numbers as arguments and return numbers.
There is nothing to re-enable.

One operational rule is documented in `docs/` because it is a research finding rather than a
secret: on a venue account shared between independent strategies, cancellation must address
strategy-owned order identifiers only. A blanket cancel-all on a shared key destroys another
strategy's resting orders. The rule is stated; no implementation of either behaviour ships here.

## Reporting

If you find anything in this repository that looks like an operational detail rather than a
research one, please open an issue describing the file and line without quoting the content.
