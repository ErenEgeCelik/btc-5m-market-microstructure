# Replay and paper coverage

Replay evaluates a modeled policy on recorded market paths. Paper execution evaluates an online
engine with simulated orders. Neither is realized trading P&L. Their agreement can check mechanics;
their disagreement can reveal missing state, timing or coverage.

In a recorded six-slot stress window, replay credited approximately +$21 while a contemporaneous
paper engine reported approximately -$31. Subsequent investigation identified cold-start regime
blindness, stale-feed handling and inventory/loss-limit problems. The numbers describe a defective
harness comparison. They do not estimate the profitability of a correctly functioning policy.

A separate earlier A/B comparison covered 157 common slots. A later audit found incorrect maker
activation and cancellation assumptions and invalidated its economic interpretation. Its original
inconclusive label must not be carried forward as though the experiment were clean.

Positive replay estimates can remain optimistic because order flow and queue access are endogenous.
The research therefore treats positive replay policy results as upper bounds to investigate, not
permission to deploy. This is a research decision convention, not a proof that every simulation
error has an upward sign.

## What can be reproduced here

| Artifact | What it establishes | What it does not establish |
|---|---|---|
| Public policy walkthrough | Actual frozen A+B parameters passed through inspectable EV/constraint functions, with synthetic book states | Historical P&L, actual order fills, or online timing availability |
| 368 W per-slot output rows | Means, paired differences, tape stability and fresh bootstrap intervals computed from the same archived simulator output | Reproduction of original event paths or independent verification of the fill model |
| Archived W summaries | Original sample counts, rebates, flatten metrics and intervals | Recovery of per-slot trading-only differences where per-slot rebates were not archived |
| D11/D15 earlier reports | Dated development sequence and original reported decision criteria | A numerical rerun of the missing original A+B+F output snapshot |
| Six-slot defective paper comparison | An observed disagreement between two harnesses on a matched stress period | An estimate of valid live policy profitability or a calibrated correction factor |

The W audit reports per-tape values and a descriptive chronological 70/30 split;
the full W period was already a model-checking sample. A+B supplied the frozen
calibration, F was the earlier held-out block, and W was a later overlapping-paper
stress test. These roles must not be collapsed into a single generic “OOS” label.

## The W discrepancy identifies more than a fill-rate problem

The historical W replay reported EVM at +123.4515 cents/slot; all eight W tape
means were positive. The public paired-row recheck confirms the arithmetic,
not a profitable strategy. The contemporaneous paper harness had cold-start
regime buffers, loss-limit halts that censored the comparison, a cap that stopped
new orders without flattening inventory, and a configuration override that did
not take effect. A later observer also found value-stale external feed periods:
ticks continued to arrive while their price barely changed through a sharp
book move. Transport liveness alone therefore did not establish usable state.

The source replay had separate optimistic mechanisms: retrospective settle
boundaries, hypothetical queue access, quantity-free proxy fill times credited
at full requested size, and ten-second calibration transferred across variable
windows. Fixing an online cold-start bug would not by itself validate those
simulation assumptions. Conversely, the broken paper loss does not identify
the economics of a corrected implementation.

There is also an execution-coordinate distinction: the replay's split-inventory
equations use synthetic Up bid/ask cash flows, while the inspected
`MakerExecutor._submit` version calls complementary **BUY** orders (Up for BID,
Down at `1-price` for ASK). Equivalent signed terminal exposure does not establish
identical cash availability, collateral reservation or rejection behavior.
The public policy module has no order client and makes no assertion that all
historical engines used one split-and-sell submission path.

Some prior narrative compared calm-paper P&L with tape P&L after dividing the
latter by two. That informal shrink factor is not a calibrated bridge between
the two harnesses and is not adopted here. Neither the six-slot stress result
nor the earlier invalid 157-slot A/B result is presented as actual trading P&L.

Source identities are in [policy provenance](../evidence/policy_experiments.json);
the [experiment table](negative-results.md) distinguishes historical reports
from the current recorded-output audit.
