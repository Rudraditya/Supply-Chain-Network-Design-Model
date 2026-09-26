"""Regression checks against the solved teaching case and model invariants."""
import copy
import unittest

from model import base_config, fixed_base_config, resize_base_config, load_case, preset, solve


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

    def test_three_modes_isolate_rerouting_resizing_and_reopening(self):
        for name in ("A · Demand mix", "B · Freight shock", "E · G1 closure"):
            with self.subTest(name=name):
                scenario = preset(name, self.data)
                reroute = solve(fixed_base_config(scenario, self.base), self.data)
                resized = solve(resize_base_config(scenario, self.base), self.data)
                redesigned = solve(scenario, self.data)
                if reroute["objective_cr"] is not None:
                    self.assertGreaterEqual(reroute["objective_cr"] + 1e-4, resized["objective_cr"])
                self.assertGreaterEqual(resized["objective_cr"] + 1e-4, redesigned["objective_cr"])
                self.assertEqual(resized["integrated_modules"]["I2"], "Closed")
                if name == "E · G1 closure":
                    self.assertEqual(resized["split_modules"]["G1"], "Closed")
                else:
                    self.assertNotEqual(resized["split_modules"]["G1"], "Closed")
        c = preset("C · I1 delay", self.data)
        fixed = solve(fixed_base_config(c, self.base), self.data)
        resized = solve(resize_base_config(c, self.base), self.data)
        redesigned = solve(c, self.data)
        self.assertIsNone(fixed["objective_cr"])
        self.assertIsNone(resized["objective_cr"])
        self.assertEqual(redesigned["status"], "optimal")
        self.assertNotEqual(redesigned["integrated_modules"]["I2"], "Closed")

    def test_open_choice_requires_site_but_optimizes_module(self):
        config = base_config(self.data)
        config["integrated_choices"]["I2"] = "Open"
        result = solve(config, self.data)
        self.assertIn(result["integrated_modules"]["I2"], {"S", "M", "L"})

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

    def test_site_capacity_changes_are_enforced_and_reported(self):
        config = base_config(self.data)
        config["integrated_clinker_capacity_pct"]["I1"] = -10.0
        config["integrated_grinding_capacity_pct"]["I1"] = 15.0
        config["split_grinding_capacity_pct"]["G1"] = 20.0
        for site, choice in (("I1", "L"), ("G1", "L")):
            config["integrated_choices" if site.startswith("I") else "split_choices"][site] = choice
        result = solve(config, self.data)
        self.assertEqual(result["status"], "optimal")
        usage = {(u["site"], u["process"]): u for u in result["site_utilization"]}
        i_large = self.data["integrated_modules"][2]
        g_large = self.data["split_modules"][2]
        self.assertAlmostEqual(usage["I1", "Clinker"]["nameplate_mtpa"], .9*i_large["clinker_mtpa"])
        self.assertAlmostEqual(usage["I1", "Grinding"]["nameplate_mtpa"], 1.15*i_large["grinding_mtpa"])
        self.assertAlmostEqual(usage["G1", "Grinding"]["nameplate_mtpa"], 1.2*g_large["grinding_mtpa"])
        self.assertTrue(all(u["utilization"] <= config["utilization"]+1e-5 for u in result["site_utilization"]))

        config["split_grinding_capacity_pct"]["G1"] = -100
        with self.assertRaisesRegex(ValueError, "Capacity change"):
            solve(config, self.data)


if __name__ == "__main__":
    unittest.main()
