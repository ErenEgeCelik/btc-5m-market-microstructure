"""Synthetic component demonstration; no empirical market result."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from btc5m_research.quote_model import single_feed_series, lagged_reference, predicted_mid
from btc5m_research.queue import RestingOrder

rows = [json.loads(line) for line in (ROOT / 'examples/synthetic_tape.jsonl').read_text().splitlines()]
ticks = [(r['t'], r['venue'], r['price']) for r in rows]
bn = single_feed_series(ticks, 'bn')
order = RestingOrder(size=2, queue_ahead=3, placed_at=0)
early = order.consume(0.02, 100)
after = order.consume(0.08, 4)
assert early == 0 and after == 1
reference = lagged_reference(bn, now=0.10, lag_s=0.05)
assert reference == 100001.0
print(json.dumps({'data':'synthetic', 'bn_ticks':len(bn), 'causal_reference':reference,
    'illustrative_probability':round(predicted_mid(reference-100000, 2, 60),6),
    'pre_activation_fill':early,'post_activation_fill':after}, indent=2))
