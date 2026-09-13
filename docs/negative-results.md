# Experiment evolution: hypotheses, controls and retained findings

The research developed models and strategies by separating three questions:
how the book prices the contract, which fills can plausibly be reached, and
what happens to inventory after a fill. A useful finding can survive even when
the policy it informed fails. The table preserves both constructive results and
the tests that changed their interpretation.

| Experiment/version | Question and control | Finding and present interpretation |
|---|---|---|
| Pricing study | Does a compact stochastic model describe quoted probabilities? Compare transformed-price structure and later held-out mids. | Descriptive pricing structure; no identified-incumbent quote schedule or standalone alpha claim. |
| Feed event correction | Does a spike separate from a randomized event control? | Alternating Coinbase/Binance levels created false spikes. Single-venue event construction replaced the merged series; earlier feed-trigger claims were withdrawn. |
| D7 fill model | Does trailing flow add discrimination? Permute flow and wall size separately. | Wall size retained the supported information; the one-parameter exponential fill model failed. Empirical bucket lookup remained a modeling input. |
| D8 original unified replay | Does directional dodge add more than a random-side pull? Inspect rebates and tape blocks separately. | Positive pooled modeled P&L, mostly rebate income, with strong regime variation. Kept an inventory ledger and matched placebo rather than equating markout with slot P&L. |
| D10 paper autopsy | Why can positive short-horizon fill markouts coexist with a losing run? | Residual inventory carried against a trend and matched-spread losses motivated a specific post-fill management experiment. |
| D11 REB, 2026-07-16 | Maker rebalance versus carry-to-200 and immediate taker exit; paired slot differences and trading-only decomposition. | Reported positive maker-exit improvement on the original A+B+F sample; weaker under alternative fill assumptions and not established across every later block. |
| D11 drift gate | Compare every fixed drift threshold with matched-frequency random skipping. | Gates failed their information test. A profitable baseline minus more skipped opportunities is not evidence of useful regime selection. |
| D12b, 2026-07-18 | Correct the initial front calculation for 50 ms POST activation. | Roughly two-thirds of apparent front value was in pre-activation prints. Those prints could not fill a newly submitted order. |
| D12 grown F | Test static front-calm at the favorable $\alpha=0$ boundary, with chronological and trimming checks. | EV(0) = −0.9845c per eligible moment, 90% interval [−1.626, −0.364], 312 moments in 193 slots. Reject this defined candidate. |
| D15 frozen EVM, 2026-07-18 | A+B calibration; F held out; compare REB, baseline and scrambled-regime EVM. | Positive conditional policy deltas under its fill/scheduler assumptions. Preserved as research about decision structure, not realized profit. |
| D16 W, 2026-07-22 | Replay the same weekend as the online paper arms. | Replay stayed positive where a defective paper engine lost. A numerical replay/paper discrepancy exposed missing online state and execution assumptions. |

## D11 and D15: the positive design findings, with their versions

The **original** 1,013-slot A+B+F report recorded REB minus baseline at
**+10.9c/slot [2.5, 19.5]**. All three then-available fresh tapes improved;
trading-only improvement was +6.4c/slot and the fraction of slots requiring
terminal flatten fell from roughly 86% to 63%. Immediate taker removal was
substantially worse, distinguishing maker exit from mere earlier risk reduction.
The alternative fill convention's paired +3.8c estimate spanned zero.

The original D15 report recorded **EVM minus REB +67.8c/slot [53, 82]** and
**EVM minus scrambled EVM +16.7c/slot [9, 24]**. The later **grown F=371-slot**
report recorded **EVM minus baseline +83.8c/slot [56.5, 111.7]** on F.
These are identified, rounded **historical reports** from the project state/log;
their original per-slot archives are not included here. They are not outputs
of the current W audit, nor pooled across sample versions.

The contribution is a controlled decomposition: book placement and inventory
management supply a common structure; regime-conditioned marginal and joint EV
change which opportunities are selected. The scrambled lookup tests the latter
while retaining the former. [Strategy code and equations](strategies.md) expose
this logic directly.

## Independently recomputed from the released W rows

The available `links_d8.json` snapshot contains **W01–W08, 368 FULL slots**.
All four primary arms were matched by slot and checked against the health index.
The public recheck preserves original rounded simulator P&L and recomputes
2,000-replicate paired slot bootstrap intervals with seed 17:

| Difference | Cents/slot | Recomputed 90% interval |
|---|---:|---:|
| EVM − base | +68.5024 | [39.35, 95.17] |
| EVM − REB | +58.7809 | [33.05, 82.62] |
| EVM − scrambled EVM | +26.5074 | [12.63, 40.80] |
| REB − base | +9.7215 | [−4.72, 23.72] |

The final row matters: the earlier REB finding does not become a blanket claim
of statistically positive improvement in every later block. These intervals
describe sampling uncertainty **conditional on the archived simulator**, not
uncertainty about queue access or model realism. The original NumPy bootstrap
used 1,000 draws and unrounded values; small interval differences are expected.

Adjacent implementation limits are material. The historical simulator omitted
the Fréchet lower joint bound, credited full REB quantities on a quantity-free
proxy fill time, reused fixed calibration across placement/window definitions,
and referenced retrospective settle-group endpoints. Its unknown-feed fallback
could treat missing information as neutral. The public decision functions repair
specific input/probability handling; these archived W outputs remain unchanged.
The [paper comparison](simulation-coverage.md) demonstrates why even positive
results across eight tapes are insufficient to establish live economics.

```bash
python estimators/policy_audit.py
python estimators/policy_audit.py --json
```

See [input definitions](../data/policy/README.md),
[source hashes and report versions](../evidence/policy_experiments.json), and
[archived summaries](../data/policy/w_archive.json). The D12 verifier retains
its separate per-moment denominator and aggregate-reproduction scope.
These results concern specified policies and periods; they do not prove that
all market making or all directional forecasting is impossible.
