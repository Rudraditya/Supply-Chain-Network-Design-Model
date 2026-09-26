"""Regression checks against the solved teaching case and model invariants."""
import copy
import unittest

from model import base_config, fixed_base_config, load_case, preset, solve


class NetworkModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_case()
        cls.base = solve(base_config(cls.data), cls.data)

    def test_base_reconciles_case_and_all_markets(self):
        result = self.base
        self.assertEqual(result["status"], "optimal")
        self.assertAlmostEqual(result["objective_cr"], 7792.260789, places=3)
        self.assertEqual(result["integrated_modules"],
                         {"I1": "L", "I2": "Closed", "I3": "L", "I4": "L", "I5": "M", "I6": "S"})
        self.assertEqual(result["split_modules"], {"G1": "L", "G2": "M", "G3": "M", "G4": "M"})
        self.assertAlmostEqual(sum(result["market_served_mt"].values()), 33.78, places=5)
        self.assertAlmostEqual(sum(result["cost_breakdown_cr"].values()), result["objective_cr"], places=5)
        self.assertTrue(all(x["km"] <= 800 for x in result["integrated_cement_flows"] + result["split_cement_flows"]))
        self.assertTrue(all(x["km"] <= 1300 for x in result["clinker_flows"]))

    def test_required_scenarios_match_excel(self):
        for label, cost in (("A · Demand mix", 7889.44409),
                            ("B · Freight shock", 8518.148393),
                            ("C · I1 delay", 8215.102262),
                            ("D · I3 limestone", 7859.641793)):
            with self.subTest(label=label):
                result = solve(preset(label, self.data), self.data)
                self.assertEqual(result["status"], "optimal")
                self.assertAlmostEqual(result["objective_cr"], cost, places=3)

    def test_fixed_base_robustness_and_infeasibility(self):
        a = solve(fixed_base_config(preset("A · Demand mix", self.data), self.base), self.data)
        self.assertAlmostEqual(a["objective_cr"], 7974.880464, places=3)
        c = solve(fixed_base_config(preset("C · I1 delay", self.data), self.base), self.data)
        self.assertEqual(c["status"], "infeasible")
        self.assertIsNone(c["objective_cr"])
        self.assertTrue(any("grinding" in note for note in c["diagnostics"]))

    def test_grinder_closure_and_material_factor(self):
        closed = preset("E · G1 closure", self.data)
        result = solve(closed, self.data)
        self.assertEqual(result["split_modules"]["G1"], "Closed")
        self.assertGreater(result["objective_cr"], self.base["objective_cr"])
        efficient = base_config(self.data)
        efficient["clinker_factor"] = .62
        result = solve(efficient, self.data)
        self.assertEqual(result["status"], "optimal")
        self.assertLess(result["objective_cr"], self.base["objective_cr"])
        clinker = sum(x["mt"] for x in result["clinker_flows"])
        split_cement = sum(x["mt"] for x in result["split_cement_flows"])
        self.assertAlmostEqual(clinker, .62 * split_cement, places=5)

    def test_invalid_input_rejected(self):
        config = base_config(self.data)
        config["integrated_choices"]["I1"] = "XL"
        with self.assertRaisesRegex(ValueError, "I1"):
            solve(config, self.data)
        config = base_config(self.data)
        config["demand_mt"][0] = -1
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            solve(config, self.data)


if __name__ == "__main__":
    unittest.main()
