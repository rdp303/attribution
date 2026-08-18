from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "sample_click_decay.csv"


def generate(seed: int = 42, periods: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", periods=periods, freq="D")

    specs = {
        "Brand Search": {"k": 4.4, "alpha": 0.72, "median_spend": 1800, "noise": 0.10},
        "Non-Brand Search": {"k": 2.6, "alpha": 0.82, "median_spend": 5200, "noise": 0.12},
        "Competitor Search": {"k": 1.6, "alpha": 0.66, "median_spend": 2600, "noise": 0.14},
    }

    rows = []
    for group, spec in specs.items():
        spend = rng.lognormal(mean=np.log(spec["median_spend"]), sigma=0.42, size=periods)
        weekday = np.array([d.weekday() for d in dates])
        spend *= 1 + 0.08 * np.sin(2 * np.pi * weekday / 7)

        expected_clicks = spec["k"] * np.power(spend, spec["alpha"])
        clicks = expected_clicks * rng.lognormal(0, spec["noise"], size=periods)
        clicks = np.maximum(1, np.round(clicks)).astype(int)

        for date, s, c in zip(dates, spend, clicks):
            rows.append(
                {
                    "date": date.date().isoformat(),
                    "campaign_group": group,
                    "spend": round(float(s), 2),
                    "clicks": int(c),
                    "observed_cpc": round(float(s / c), 4),
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = generate()
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df):,} rows to {OUT}")
