import unittest

import numpy as np
import pandas as pd

from attribution_models import (
    attribute_conversions,
    channel_summary,
    model_share_matrix,
)


class MultiTouchAttributionTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(
            [
                ["A", "2025-01-01T00:00:00Z", "YouTube", 0, 0],
                ["A", "2025-01-03T00:00:00Z", "Meta", 0, 0],
                ["A", "2025-01-05T00:00:00Z", "Paid Search", 1, 100],
                ["B", "2025-02-01T00:00:00Z", "Meta", 0, 0],
                ["B", "2025-02-02T00:00:00Z", "Email", 1, 200],
                ["C", "2025-03-01T00:00:00Z", "Organic", 0, 0],
            ],
            columns=[
                "journey_id",
                "touch_time",
                "channel",
                "converted",
                "conversion_value",
            ],
        )

    def test_first_touch_credit(self):
        credited = attribute_conversions(self.df, "first_touch")
        summary = credited.groupby("channel")["conversion_credit"].sum().to_dict()
        self.assertEqual(summary["YouTube"], 1.0)
        self.assertEqual(summary["Meta"], 1.0)
        self.assertEqual(summary["Paid Search"], 0.0)

    def test_last_touch_credit(self):
        summary = channel_summary(self.df, "last_touch").set_index("channel")
        self.assertEqual(summary.loc["Paid Search", "conversion_credit"], 1.0)
        self.assertEqual(summary.loc["Email", "conversion_credit"], 1.0)

    def test_linear_credit_sums_to_conversions(self):
        credited = attribute_conversions(self.df, "linear")
        self.assertAlmostEqual(credited["conversion_credit"].sum(), 2.0)
        self.assertAlmostEqual(credited["revenue_credit"].sum(), 300.0)

    def test_position_based_three_touch_weights(self):
        credited = attribute_conversions(self.df, "position_based")
        journey_a = credited[credited["journey_id"] == "A"]
        np.testing.assert_allclose(journey_a["weight"].to_numpy(), [0.4, 0.2, 0.4])

    def test_time_decay_favors_later_touches(self):
        credited = attribute_conversions(self.df, "time_decay", half_life_days=2)
        journey_a = credited[credited["journey_id"] == "A"]
        weights = journey_a["weight"].to_numpy()
        self.assertTrue(weights[2] > weights[1] > weights[0])
        self.assertAlmostEqual(weights.sum(), 1.0)

    def test_model_matrix_has_all_models(self):
        matrix = model_share_matrix(self.df)
        self.assertEqual(
            set(matrix.columns),
            {"first_touch", "last_touch", "linear", "time_decay", "position_based"},
        )


if __name__ == "__main__":
    unittest.main()
