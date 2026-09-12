"""The published verdict must be reproducible, pinned, and tamper-evident.

This is the repository's central promise: the decision rule is applied to fixed
aggregate statistics, and neither the rule nor the statistics can drift without the
test failing.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_INPUT = ROOT / "evidence" / "links_d12.json"
COMMITTED_VERDICT = ROOT / "evidence" / "d12_public_verdict.json"
VERIFIER = ROOT / "estimators" / "d12_public_verifier.py"

EXPECTED_INPUT_SHA256 = "428ba2de8fe47fc1e867cc8fcbee706b9fd23f16e5eceb9d8c2db1efd5c48010"


def _load_verifier():
    spec = importlib.util.spec_from_file_location("d12_public_verifier", VERIFIER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestPublishedVerdict(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.verifier = _load_verifier()
        cls.verdict = cls.verifier.build_verdict(EVIDENCE_INPUT)
        cls.committed = json.loads(COMMITTED_VERDICT.read_text(encoding="utf-8"))

    def test_evidence_input_is_byte_pinned(self) -> None:
        digest = hashlib.sha256(EVIDENCE_INPUT.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            EXPECTED_INPUT_SHA256,
            "the aggregate evidence changed; the published conclusion no longer describes it",
        )

    def test_verdict_records_the_hash_of_its_own_input(self) -> None:
        self.assertEqual(self.verdict["source"]["sha256"], EXPECTED_INPUT_SHA256)

    def test_committed_verdict_matches_a_fresh_recomputation(self) -> None:
        rendered = self.verifier.canonical_bytes(self.verdict)
        self.assertEqual(
            COMMITTED_VERDICT.read_bytes(),
            rendered,
            "run the verifier without --check to refresh the committed verdict",
        )

    def test_decision_is_dead(self) -> None:
        self.assertEqual(self.verdict["decision"], "DEAD")

    def test_metric_is_per_eligible_decision_moment(self) -> None:
        """Not per slot. The unit has been misquoted before and changes the magnitude."""
        self.assertEqual(self.verdict["metric"]["unit"], "cents per eligible decision moment")

    def test_sample_size_is_as_documented(self) -> None:
        self.assertEqual(self.verdict["sample"]["fresh_moments"], 312)
        self.assertEqual(self.verdict["sample"]["fresh_slots"], 193)

    def test_uncertainty_is_clustered_on_slots_not_fills(self) -> None:
        self.assertEqual(self.verdict["sample"]["uncertainty_unit"], "slot")

    def test_fresh_interval_excludes_zero_from_above(self) -> None:
        low, high = self.verdict["fresh_oos"]["ci90"]
        self.assertAlmostEqual(low, -1.626, places=3)
        self.assertAlmostEqual(high, -0.364, places=3)
        self.assertLess(high, 0.0)

    def test_discovery_blocks_were_positive(self) -> None:
        """The honest part: this policy looked real before the fresh block arrived."""
        blocks = self.verdict["block_stability"]
        self.assertGreater(blocks["A_ev0"], 0.0)
        self.assertGreater(blocks["B_ev0"], 0.0)
        self.assertLess(blocks["F_ev0"], 0.0)
        self.assertFalse(blocks["fresh_sign_stable"])

    def test_chronological_split_flips_sign(self) -> None:
        oos = self.verdict["chronological_oos"]
        self.assertGreater(oos["first_70_ev0"], 0.0)
        self.assertLess(oos["last_30_ev0"], 0.0)
        self.assertFalse(oos["passed"])

    def test_rejection_survives_removing_the_worst_slot(self) -> None:
        trimmed = self.verdict["fresh_oos"]["ev0_after_removing_each_slot_once_worst_case"]
        self.assertLess(trimmed, 0.0, "the verdict is not driven by a single outlier slot")

    def test_rejection_holds_at_the_favourable_bound_of_the_unknown(self) -> None:
        self.assertTrue(self.verdict["fresh_oos"]["best_case_kill"])

    def test_domain_disclaims_any_live_profit_claim(self) -> None:
        self.assertIn("no live-profit claim", self.verdict["domain"])

    def test_external_wording_is_scoped_to_replay(self) -> None:
        self.assertIn("replay", self.verdict["external_wording"])

    def test_queue_permutation_collapses_fill_discrimination(self) -> None:
        """Control: fill information sits in visible queue size, not trailing flow."""
        controls = self.verdict["artifact_controls"]["side_split_fill_mechanism"]
        for side in ("ask", "bid"):
            self.assertGreater(controls[f"{side}_real"], 0.3)
            self.assertLess(abs(controls[f"{side}_queue_permuted"]), 0.05)
            self.assertGreater(controls[f"{side}_lambda_permuted"], 0.3)

    def test_regime_labels_outperform_shuffled_labels(self) -> None:
        placebo = self.verdict["artifact_controls"]["regime_label_placebo"]
        self.assertGreater(placebo["real_delta_cents"], 10 * placebo["shuffled_delta_cents"])


if __name__ == "__main__":
    unittest.main()
