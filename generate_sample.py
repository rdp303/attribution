from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

from attribution import standard_scenarios


CAMPAIGNS = [
    ("1001", "Prospecting | Broad", 18500, 1820000, 39200, 228, 111),
    ("1002", "Prospecting | Lookalike", 13750, 1260000, 31100, 191, 104),
    ("1003", "Retargeting | 30 Day", 8250, 415000, 18400, 217, 118),
    ("1004", "Creative Test | Video", 5900, 690000, 14350, 73, 96),
    ("1005", "Existing Customer | Upsell", 4100, 188000, 7800, 119, 126),
]

CLICK_FACTOR = {None: 0.0, "1d_click": 0.72, "7d_click": 0.93, "28d_click": 1.00}
VIEW_FACTOR = {None: 0.0, "1d_view": 0.11, "7d_view": 0.18, "28d_view": 0.23}


def main() -> None:
    random.seed(7)
    records = []
    for scenario in standard_scenarios():
        for entity_id, name, spend, impressions, clicks, base_conv, aov in CAMPAIGNS:
            click_credit = CLICK_FACTOR[scenario.click_window]
            view_credit = VIEW_FACTOR[scenario.view_window]
            combined_factor = min(1.19, click_credit + view_credit * (1 - click_credit * 0.35))
            if scenario.click_window is None:
                combined_factor = view_credit
            if scenario.view_window is None:
                combined_factor = click_credit
            noise = random.uniform(0.985, 1.015)
            conversions = round(base_conv * combined_factor * noise, 1)
            value = round(conversions * aov * random.uniform(0.98, 1.02), 2)
            records.append(
                {
                    "entity_id": entity_id,
                    "entity_name": name,
                    "scenario_key": scenario.key,
                    "scenario_label": scenario.label,
                    "spend": spend,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "conversion_value": value,
                }
            )

    path = Path("data/sample_attribution.csv")
    path.parent.mkdir(exist_ok=True)
    pd.DataFrame(records).to_csv(path, index=False)
    print(path)


if __name__ == "__main__":
    main()
