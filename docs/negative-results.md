# Experiments and revisions

| Stage | Observation | Final treatment |
|---|---|---|
| Pricing study | A compact model tracked broad market-mid structure | Useful description; no identified-maker or profitable-signal claim |
| Feed event construction | Alternating venue ticks produced false spikes | Build signal events from one venue |
| Queue information | Trailing-flow information did not survive the relevant permutation control | Retain visible queue size as the supported predictor within the virtual-join definition |
| Early front replay | Discovery blocks were positive | Superseded by corrected latency and fresh-data evaluation |
| Maker activation correction | Pre-activation prints contributed apparent fills | Begin eligibility for execution only after activation |
| Grown fresh block | EV(0) negative, including trimmed and chronological checks | Reject the specified static-front candidate |
| Inventory rebalancing and EV policy | Positive replay deltas under declared controls | Retain as model-dependent upper bounds |
| Paper comparisons | Incorrect execution assumptions and stress-window defects | Invalidated economics; retain operational diagnosis |

The D12 aggregate records discovery-block EV(0) of approximately +0.34 and +0.43 cents per moment,
against -0.9845 on the grown fresh block. The public verifier checks the fresh estimate, interval,
chronological split and worst-slot-trimmed result against its encoded decision rule.
It does not implement every upstream placebo or calculate the underlying confidence intervals.

These results concern tested policy families and measured periods. They do not prove that all market
making, all retail participation or all directional forecasting is impossible.
