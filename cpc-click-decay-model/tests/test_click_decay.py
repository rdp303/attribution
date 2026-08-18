import unittest

import numpy as np
import pandas as pd

from click_decay import fit_by_group, fit_power_curve, scenario_table


class ClickDecayTests(unittest.TestCase):
    def test_recovers_power_exponent(self):
        spend = np.geomspace(100, 10000, 60)
        clicks = 3.2 * spend ** 0.75
        df = pd.DataFrame({"spend": spend, "clicks": clicks})
        curve = fit_power_curve(df, "spend", "clicks")
        self.assertAlmostEqual(curve.alpha, 0.75, places=6)
        self.assertAlmostEqual(curve.r_squared, 1.0, places=6)

    def test_marginal_cpc_exceeds_average_when_alpha_below_one(self):
        spend = np.geomspace(100, 10000, 60)
        clicks = 4.0 * spend ** 0.7
        curve = fit_power_curve(pd.DataFrame({"spend": spend, "clicks": clicks}), "spend", "clicks")
        self.assertGreater(curve.marginal_cpc(1000), curve.average_cpc(1000))

    def test_group_fit(self):
        rows = []
        for group, alpha in [("A", 0.6), ("B", 0.85)]:
            spend = np.geomspace(100, 5000, 20)
            clicks = 2.0 * spend ** alpha
            rows.extend({"group": group, "spend": s, "clicks": c} for s, c in zip(spend, clicks))
        curves = fit_by_group(pd.DataFrame(rows), "group", "spend", "clicks")
        self.assertEqual(set(curves), {"A", "B"})
        self.assertLess(curves["A"].alpha, curves["B"].alpha)

    def test_scenario_table_has_all_multipliers(self):
        spend = np.geomspace(100, 5000, 20)
        clicks = 2.0 * spend ** 0.8
        curve = fit_power_curve(pd.DataFrame({"spend": spend, "clicks": clicks}), "spend", "clicks")
        table = scenario_table([curve], multipliers=[0.5, 1.0, 2.0])
        self.assertEqual(table.shape[0], 3)
        self.assertListEqual(table["spend_multiplier"].tolist(), [0.5, 1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
