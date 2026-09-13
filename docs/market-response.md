# Market response: observed feed moves and book repricing

The question was mechanical: **after a price move is observed, when and how does the binary book
absorb it?** It differs from predicting the next underlying move. It motivated book-derived quote
levels, response-aware timing and cancellation of the threatened side.

## D4: first response and its denominator

Use Binance arrival-time displacement over 200 ms, threshold grid $3/$5/$8 and one-second deduplication.
D4 samples FULL slots at offsets `[10,200)`, takes a book as-of no older than 0.5 s and scans at most
3 s for the **first nonzero midpoint move**. A gap over 1.5 s ends the scan. An opposite first move is
wrong-direction even if a later move agrees. No move before the horizon or break is historically a
fizzle; the public helper exposes the structural-break status separately.

The archived $5 row contains 13,782 events. Fizzles are 3.11%; among non-fizzles, 87.05% of first moves
agree with the spike, versus 49.48% for random-time/random-direction placebo. **Median delay among
correct confirmations is 275 ms**. Older overview prose rounded this to 280 ms; preserve the archived
D4 value and the distinct D14 result separately.

`conf0.4=0.6523` means confirmation within 400 ms **conditional on eventual correct confirmation**.
From rounded fields, the unconditional product is

$$P(\text{correct by }T)\approx(1-f_{\mathrm{fizzle}})(1-f_{\mathrm{wrong}})
 P(L\le T\mid\text{correct confirmation}).$$

The auditor recomputes that product, not the original event count or confidence interval. Placebo n
and per-tape counts were not retained by D4; D4b has its own separate per-tape counts.

## D4b: delayed absorption and saturation

After a direction-correct first response, define

$$B_i(h)=100d_i[m(t_{c,i}+h)-m(t_{s,i})],\quad
S_i=|F(t_{s,i}+1)-F(t_{s,i}-0.2)|,\quad
r_b(h)=\frac{\operatorname{mean}_{i\in b}B_i(h)}{\operatorname{mean}_{i\in b}S_i}.$$

The bucket uses **future realized** one-second feed movement; this is an explanatory event study,
not a decision-time predictor. Book horizons start at confirmation. Feed ages >2 s are dropped;
book ages >1.5 s drop that horizon only. The archived ratio uses the full bucket's mean S even if a
few book observations are missing; exact denominators are preserved as `n` and `b_n`.

| Realized feed displacement | Bucket n | Book response at confirmation +2 s (c) | Transfer (c/$) |
|---|---:|---:|---:|
| $3–5 | 4,452 | 2.8237 | 0.7157 |
| $5–8 | 5,178 | 3.8738 | 0.6079 |
| $8–12 | 3,770 | 5.0318 | 0.5173 |
| $12–20 | 2,755 | 6.4557 | 0.4311 |
| >=$20 | 964 | 8.6921 | 0.3109 |

Decreasing response per dollar describes saturation, not proof of harvestable mispricing. The
fixed-sigma normal-model derivative was a comparison curve, not a fitted causal benchmark. Placebos
are themselves conditioned on direction-correct confirmation; their positive signed response is
selection-induced and is not an alpha estimate.

## D14: calm-to-spike anatomy

D14 uses offsets 10–288 s, a two-second horizon, thresholds $5/$8/$12 and calm measured **before the
spike's own 200 ms window**. The preceding two-second Binance range must be <$3 and touches unchanged
for 0.5 s at that pre-spike reference. Book moves inside the spike window remain included and reported.
The $5 group has 5,767 events and 5,767 random calm placebos; $8/$12 have 2,546/970 events and overlap
the lower-threshold group. These sample definitions differ from D4.

At each matched top-five price level:

$$C_\ell=\max[0,Q_{\ell,\mathrm{before}}-Q_{\ell,\mathrm{after}}-V_\ell],\quad
A_\ell=\max[0,Q_{\ell,\mathrm{after}}-Q_{\ell,\mathrm{before}}].$$

Trades use `(previous snapshot,current snapshot]`, strictly after the event for the first pair.
Residuals belong to the later snapshot's time bin. `C` is **inferred unexplained removal**, not an
observed cancellation message: top-five migration, missed trades and replenishment can change its
meaning. `A` is visible net addition, not gross new-order volume. `decompose_depth` implements this.

| Time after $5 spike | Threat-side traded shares/event | Calm-placebo shares/event |
|---|---:|---:|
| 0–50 ms | 4.45 | 3.20 |
| 50–100 ms | 4.73 | 3.09 |
| 100–200 ms | 15.71 | 8.89 |
| 200–500 ms | 128.28 | 58.63 |
| 0.5–1 s | 139.31 | 69.27 |
| 1–2 s | 183.99 | 125.95 |

Mean event-level inferred-removal fraction at 50 ms is 6.14%, versus 3.03% placebo; archived
slot-bootstrap 90% interval `[5.7520,6.5426]%`. It reaches 33.53% by 200 ms. These are means of
event-level fractions, not pooled volume ratios, and cannot be reconstructed from mean-volume arrays.
The first **direction-agreeing** midpoint move has median 280 ms, among the 92.9% moving that way within
2 s. Unlike D4, this permits an earlier opposite move: the two medians are not identical estimands.

At $8, fresh F has 237 events. Threat-side volume/event at 200–500 ms is 183.10 shares versus 141.80
in A and 100.38 in B; at 1–2 s it is 349.23 versus 202.02/210.21. First-removal-before-first-trade shares
are 75.9% in F, 90.5% in A and 92.0% in B. That denominator includes events with only one event type,
excludes neither-type events and is not our chance of beating a competing maker. The fresh sample
is associated with heavier directional flow; this does not identify a causal policy benefit.

## Reproduction contract

Inputs and formulas were fixed before the publication audit. All aggregate fields are preserved in
[data/mechanics](../data/mechanics/README.md), with source hashes. Run
`python estimators/mechanics_audit.py --json` to recompute direction products, transfer ratios,
count reconciliation and flow ratios. Medians, uncertainty and placebo statistics remain archived
estimates; original event-level observations are not included. The synthetic walkthrough separately
tests time alignment, wrong-first-response handling and top-level depth decomposition.

Sources: `d4_confirm_map.main.measure`, `d4b_transfer.main.confirm`, `book_resp`,
`d14_spike_anatomy.main.clean_at`, `measure`, `agg`, and `boot_ci90`.
