# Implemented policies and their decision inputs

The design question was where and when to expose split inventory, and how to
reduce the leg left after a one-sided fill. A compact pricing model helped
describe market response; executable quote levels came from the book.

The split-pair formulation and the replay below use **synthetic Up-book
coordinates**. They should not be mistaken for a description of every historical
order-submission path. In the separately inspected `live/mm_maker.py` version,
`MakerExecutor._submit` implements a BID by buying Up at `price`, and an ASK by
buying Down at `1-price`; both call `ClobClient.post_only_buy_limit`. That
selected executor acquires complementary tokens rather than selling pre-split
inventory. The signed terminal exposure can be expressed in the same synthetic
coordinate system, while collateral requirements, reservation and balance
availability remain distinct execution mechanics. See
[the version-specific execution mapping](data-engineering.md) and
[its source hashes](../evidence/mechanics_experiments.json).

## Baseline: settle, choose a level, dodge, flatten

The unified D8 replay used decision times between 10 and 200 seconds into a
five-minute slot. It detected stable touch groups and a quiet single-venue feed
window, then quoted five shares per side. At a spread of at least three cents,
each side improved the touch by one cent; otherwise it joined the visible touch.
The three-cent rule prevents two one-tick improvements from meeting at the same
price in a two-cent book.

Quotes became eligible 50 ms after decision. A Binance move of at least $5 over
200 ms triggered a 50 ms delayed cancellation of the threatened side: an upward
move threatens the Up ask, and a downward move threatens the synthetic Up bid.
The book provided a fallback trigger. The other side could remain until the next
settle boundary. A signed-inventory clamp blocked exposure-increasing quotes
at $|I|\ge15$ shares; remaining inventory was flattened at 200 seconds using
book prices and the historical taker fee model.

These 50 ms maker assumptions are separate from the historical 250–330 ms
taker path and the 218 ms cancel tail under load. They are not interchangeable
latency estimates.

## REB: make the residual-inventory problem explicit

The original baseline waited until the terminal flatten boundary to resolve
residual exposure. D10's paper autopsy found individually favorable five-second
fill markouts alongside losses from inventory held against a trend. D11 added
REB: at a settle boundary with $|I|\ge5$ shares and no new baseline episode,
quote the reducing side for $|I|$ shares. It follows the same book placement,
activation and dodge rules; an unfilled quote rolls at the next boundary.

Controls separated the mechanism:

- **base:** carry residual inventory to the scheduled flatten boundary;
- **TNOW:** immediately remove eligible residual exposure with a fee-paying
  taker action at the next settle boundary;
- **REB:** seek a maker exit, retaining cancellation protection;
- **drift gates:** skip episodes beyond 15, 25 or 40 dollars of trailing
  300-second absolute Binance drift;
- **matched-frequency random skips:** test whether a gate adds information
  beyond simply quoting less. Gates do not suppress reducing REB actions.

## EVM: frozen inputs, explicit branch values, constrained actions

The D15 policy evaluated every settle window, rather than only baseline entry
episodes. Its recorded A+B calibration is included as
[`frozen_calibration.json`](../data/policy/frozen_calibration.json):

| Input | Construction used by the selector |
|---|---|
| Regime | trailing 1.5-second Binance move: $|m|<3$ dollars calm; $|m|\ge8$ directional; intermediate neutral |
| JOIN marginal fills | empirical buckets of $x=\lambda\cdot10/r_0$ |
| Front marginal fills | frozen A/B rates 0.4464 / 0.4787 |
| Drift cost | frozen ask/bid means by regime, cents/share |
| Joint adjustment | frozen $\rho=1.036$ |
| Rebate | historical $1.4p(1-p)$ cents/share at the quote price |

For example the recorded ask drift is +1.976c in an upward regime and −0.351c
in a downward regime; the bid values are −0.010c and +2.008c respectively.
This encodes conditional fill quality, not an assumed unconditional spot-price
forecast. The actual calibration export conditions drift on the decision-time
regime (`R0c`). Separate D12 analyses also use future-window regime labels;
those labels are not inputs to this selector.

The selector compares $\{0,E_A,E_B,E_2\}$ from the
[branch equations](mdp-ev-chain.md). With small inventory it takes the feasible
positive maximum. At $I\ge5$, the reducing A quantity is forced to $I$, even
if its one-step EV is negative; a B clip is optional if positive and within the
clamp. For $I\le-5$ the roles reverse. Thus EVM embeds REB as a constraint,
not an optimized continuation-value term. The paired unit EV is not a valuation
of unequal REB quantities.

The public walkthrough uses a **synthetic** 49/52-cent book and actual frozen
parameters. It selects both sides in calm, B in an upward move and A in a
downward move. At ten shares long during an upward move it still mandates a
reducing A quote, illustrating the difference between reward ranking and risk
constraints. The quote levels remain 51/50 cents in every regime.

```bash
python examples/policy_walkthrough.py
python examples/policy_walkthrough.py --json
```

The scrambled-brain control preserves placement, inventory constraints and the
rest of the engine while swapping regime lookup labels $R_0\leftrightarrow R_+$
and $R_-\leftrightarrow\mathrm{NEUT}$. The comparison asks whether conditional
drift information adds value beyond the shared structure. It is one deterministic
placebo, not an exhaustive randomization distribution.

## Historical implementation limits and public corrections

The extracted public selector has valid Fréchet branch probabilities, preserves
genuine zero calibration inputs, and keeps unknown feed state separate from
neutral. The historical implementation lacked the lower joint bound, used
`value or fallback` and mapped unknown state to NEUT. The public checks document
these changes; they do not retroactively correct the archived results.

The replay's fill walk was independent of the requested REB quantity, but a
successful proxy fill credited the entire $|I|$ amount. In addition, same-window
fills were evaluated from the starting inventory without an intra-window
adaptive re-decision. JOIN drift/joint estimates were reused for front quotes,
front-calm marginal rates for other regimes, and ten-second probabilities to
rank variable-duration windows. These choices limit what its positive results establish.
No true queue-order bound or verified execution capacity is claimed.

Settle groups were reconstructed from future touch-event gaps shorter than
0.5 seconds, with entry referenced to the group's last event. An online engine
cannot know at that event that the group has ended. The replay did not establish
equivalent online availability after the necessary confirmation delay. Public
`DecisionState` accepts an already-observed state and does not reproduce or
silently validate this retrospective scheduler.

For the actual controlled comparisons and their versions, continue to
[experiment evolution](negative-results.md) and [replay/paper coverage](simulation-coverage.md).
The [risk comparison](binary-risk-and-market-making.md) explains which
Avellaneda–Stoikov assumptions apply to the binary payoff; this strategy did not
use that formula as a quote-centering rule.
