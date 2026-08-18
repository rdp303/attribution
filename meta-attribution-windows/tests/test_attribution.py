import unittest

import pandas as pd

from attribution import AttributionScenario, aggregate_scenarios, attribution_matrix, standard_scenarios
from meta_api import MetaAPIError, extract_action_metric


class AttributionTests(unittest.TestCase):
    def test_standard_scenarios_are_unique(self):
        scenarios = standard_scenarios()
        self.assertEqual(len(scenarios), 15)
        self.assertEqual(len({s.key for s in scenarios}), 15)

    def test_scenario_label(self):
        s = AttributionScenario("7d_click", "1d_view")
        self.assertEqual(s.key, "7d_click+1d_view")
        self.assertEqual(s.label, "7d click + 1d view")

    def test_extract_generic_value(self):
        rows = [{"action_type": "purchase", "value": "12", "1d_click": "8"}]
        self.assertEqual(extract_action_metric(rows, "purchase", ["1d_click", "1d_view"]), 12.0)

    def test_does_not_sum_overlapping_windows(self):
        rows = [{"action_type": "purchase", "1d_click": "8", "1d_view": "5"}]
        with self.assertRaises(MetaAPIError):
            extract_action_metric(rows, "purchase", ["1d_click", "1d_view"])

    def test_summary_metrics(self):
        df = pd.DataFrame(
            [
                {"scenario_key": "1d_click", "scenario_label": "1d click", "spend": 100, "impressions": 1000, "clicks": 50, "conversions": 5, "conversion_value": 250},
                {"scenario_key": "1d_click", "scenario_label": "1d click", "spend": 50, "impressions": 500, "clicks": 20, "conversions": 5, "conversion_value": 250},
            ]
        )
        summary = aggregate_scenarios(df).iloc[0]
        self.assertEqual(summary["cpa"], 15)
        self.assertAlmostEqual(summary["roas"], 500 / 150)

    def test_matrix_shape(self):
        scenarios = standard_scenarios(include_single_window=False)
        rows = []
        for i, s in enumerate(scenarios):
            rows.append({"scenario_key": s.key, "scenario_label": s.label, "spend": 100, "impressions": 1000, "clicks": 50, "conversions": i + 1, "conversion_value": (i + 1) * 100})
        summary = aggregate_scenarios(pd.DataFrame(rows))
        matrix = attribution_matrix(summary, "roas")
        self.assertEqual(matrix.shape, (3, 3))


if __name__ == "__main__":
    unittest.main()
