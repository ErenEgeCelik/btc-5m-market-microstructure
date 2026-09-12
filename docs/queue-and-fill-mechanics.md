# Queue and fill mechanics

Level-2 records contain visible size and trades, not the identity or rank of a hypothetical new order.
The reference model starts behind visible depth and walks subsequent flow. It cannot reproduce how
other participants would react to our additional order.

The historical maker decision cell uses 50 ms activation and 50 ms cancellation latency. Measured
maker POST was 24–50 ms; cancel median 23–50 ms, with a roughly 218 ms tail under load. The 250–330 ms
figures in older notes concern the taker path and must not replace maker assumptions.

`RestingOrder.consume` ignores trades before activation. Cancellation leaves the order fillable until
the modeled cancel arrival. The two queue walks credit either trades alone or trades plus unexplained
size reductions. These are sensitivity scenarios, not guaranteed statistical bounds on real fills.
Hidden size, priority, replenishment and changing depth at activation can place reality outside them.

The clean-index utilities reject event windows overlapping identified feed dropouts. A book that has
not changed while exchange feeds move may be stale rather than stable. The upstream study detected
freezes up to 32 seconds. Signal events are built from Binance alone to avoid cross-venue artifacts.

Never infer a fill probability from a denominator containing only filled orders. Keep all eligible
decision moments, fill-conditioned markouts and slot-level P&L in separate tables.
