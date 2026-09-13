# Evidence coverage

The [contribution map](../CONTRIBUTIONS.md) connects the research to methods and code; the
[claim register](../evidence/claim_ledger.yaml) records what the evidence supports. Explanatory
pricing fit, forward prediction, conditional book response, modeled execution value and realized
returns have distinct targets.

## Available to inspect and rerun

The public release contains a 358-row pricing-feature study, frozen mechanics summaries, 368
recorded per-slot simulator outputs, a policy calibration table, reference implementations and
synthetic demonstrations. [Reproduction instructions](../REPRODUCIBILITY.md) distinguish input
refitting, recorded-output rechecks, aggregate audits and analytical examples.

The source records pin inspected private files, identify important functions and document extraction.
They are provenance for the author's release, not publicly accessible upstream raw data. Current
source hashes can identify inspected code that evolved after an older output was produced; such
cases are labeled instead of assigning a false producer version.

## Scope of interpretation

| Evidence | Appropriate interpretation | Remaining question |
|---|---|---|
| Brownian-probit and feature fits | A measured description of market mids or implied scale | Causal feature availability, independent model selection, probability calibration |
| Feed/book event aggregates | Conditional direction, timing and confirmation under a specified selection | Effects of receiver clocks, conditioning, health coverage and sampling |
| Queue and fill proxies | Sensitivity to explicit depletion and cancellation conventions | Real queue rank, hidden priority and quantity-dependent access |
| Paired policy output recheck | Differences between historical simulated policies on the same slots | Whether modeled fills and inventory handling transfer to execution |
| D12 negative fresh EV(0) | Rejection of the specified static-front candidate within the recorded model | No blanket rejection of every maker policy |
| Broken paper diagnostics | Harness, data and accounting faults requiring correction | Clean live strategy economics cannot be inferred from that run |

Positive tape results remain model-dependent upper bounds or execution-test targets. The
`pes`/`opt` queue conventions are not mathematically proven bounds on real fills. In particular,
the historical rebalancing simulator did not establish fill probability for the full requested
quantity. Slot bootstrapping does not remove dependence across adjacent slots.

The empirical programme uses historical point settlement. Current contract rules and fee schedules
are outside its scope. The public package does not identify a market participant's private model
or claim a current tradable edge. The [experiment history](negative-results.md) retains the
positive design observations as well as controls, revisions and rejected candidates.
