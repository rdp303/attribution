from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "data" / "sample_journeys.csv"

CHANNELS = ["Meta", "Paid Search", "YouTube", "Email", "Organic", "Direct"]

# Channel-specific tendency to appear earlier or later in a journey.
START_PROBS = np.array([0.26, 0.18, 0.24, 0.06, 0.18, 0.08])
MID_PROBS = np.array([0.22, 0.26, 0.16, 0.12, 0.16, 0.08])
END_PROBS = np.array([0.13, 0.31, 0.07, 0.13, 0.12, 0.24])


def generate(seed: int = 42, n_journeys: int = 1200) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2025-01-01", tz="UTC")
    rows = []

    for journey_num in range(1, n_journeys + 1):
        n_touches = int(np.clip(rng.poisson(2.4) + 1, 1, 7))
        journey_start = start + pd.Timedelta(days=int(rng.integers(0, 365)))

        channels = []
        for idx in range(n_touches):
            if idx == 0:
                probs = START_PROBS
            elif idx == n_touches - 1:
                probs = END_PROBS
            else:
                probs = MID_PROBS
            channels.append(rng.choice(CHANNELS, p=probs / probs.sum()))

        # Conversion probability increases with deeper journeys, but is not guaranteed.
        unique_paid = len(set(channels) & {"Meta", "Paid Search", "YouTube"})
        logit = -1.8 + 0.34 * n_touches + 0.18 * unique_paid
        conversion_prob = 1 / (1 + np.exp(-logit))
        converted = int(rng.random() < conversion_prob)

        value = 0.0
        if converted:
            value = round(float(np.exp(rng.normal(np.log(180), 0.45))), 2)

        elapsed_hours = 0
        for idx, channel in enumerate(channels):
            if idx:
                elapsed_hours += int(rng.integers(6, 96))
            touch_time = journey_start + pd.Timedelta(hours=elapsed_hours)

            rows.append(
                {
                    "journey_id": f"J{journey_num:05d}",
                    "touch_time": touch_time.isoformat(),
                    "channel": channel,
                    "converted": converted if idx == n_touches - 1 else 0,
                    "conversion_value": value if idx == n_touches - 1 and converted else 0.0,
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df = generate()
    df.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(df):,} touchpoints across {df['journey_id'].nunique():,} journeys to {OUTPUT}")
