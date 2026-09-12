import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from btc5m_research.ev_chain import joint_fill_probability

class JointProbabilityTests(unittest.TestCase):
    def test_high_marginals_cannot_imply_negative_no_fill_probability(self):
        self.assertAlmostEqual(joint_fill_probability(.8,.8,0),.6)

    def test_four_outcomes_form_a_distribution_at_boundaries_and_interior(self):
        for a in [0,.2,.5,.8,1]:
            for b in [0,.2,.5,.8,1]:
                for rho in [0,.5,1,9]:
                    j=joint_fill_probability(a,b,rho)
                    weights=[j,a-j,b-j,1-a-b+j]
                    self.assertTrue(all(x>=-1e-12 for x in weights),(a,b,rho,weights))
                    self.assertAlmostEqual(sum(weights),1)
