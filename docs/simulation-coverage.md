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
