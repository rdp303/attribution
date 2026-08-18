#!/usr/bin/env python3
"""Generate a reproducible synthetic weekly dataset for the Robyn MMM demo."""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
WEEKS = 156
OUT = Path(__file__).parent / "data" / "sample_mmm.csv"


def adstock(values: list[float], theta: float) -> list[float]:
    output: list[float] = []
    previous = 0.0
    for value in values:
        current = value + theta * previous
        output.append(current)
        previous = current
    return output


def saturation(values: list[float], scale: float) -> list[float]:
    return [math.log1p(value / scale) for value in values]


def clipped_normal(rng: random.Random, mean: float, sd: float, floor: float) -> float:
    return max(floor, rng.gauss(mean, sd))


def main() -> None:
    rng = random.Random(SEED)
    dates = [date(2023, 1, 2) + timedelta(days=7 * i) for i in range(WEEKS)]

    facebook_impressions = []
    ppc_impressions = []
    youtube_impressions = []

    for i in range(WEEKS):
        facebook_impressions.append(
            max(
                200_000,
                800_000
                + 180_000 * math.sin(2 * math.pi * i / 13)
                + rng.gauss(0, 90_000),
            )
        )
        ppc_impressions.append(
            max(
                120_000,
                420_000
                + 90_000 * math.cos(2 * math.pi * i / 17)
                + rng.gauss(0, 45_000),
            )
        )
        youtube_impressions.append(
            max(
                250_000,
                1_100_000
                + 250_000 * math.sin(2 * math.pi * i / 21 + 0.7)
                + rng.gauss(0, 130_000),
            )
        )

    facebook_spend = [
        imp / 1000 * clipped_normal(rng, 11.5, 1.2, 8.0)
        for imp in facebook_impressions
    ]
    ppc_spend = [
        imp / 1000 * clipped_normal(rng, 18.0, 2.0, 13.0)
        for imp in ppc_impressions
    ]
    youtube_spend = [
        imp / 1000 * clipped_normal(rng, 8.0, 1.0, 5.5)
        for imp in youtube_impressions
    ]

    fb_effect = saturation(adstock(facebook_impressions, 0.25), 250_000)
    ppc_effect = saturation(adstock(ppc_impressions, 0.10), 120_000)
    youtube_effect = saturation(adstock(youtube_impressions, 0.45), 350_000)

    rows = []
    for i in range(WEEKS):
        trend = 0.35 * i
        seasonality = (
            18 * math.sin(2 * math.pi * i / 52)
            + 8 * math.cos(2 * math.pi * i / 26)
        )
        baseline = 280 + trend + seasonality
        expected_signups = (
            baseline
            + 32 * fb_effect[i]
            + 40 * ppc_effect[i]
            + 24 * youtube_effect[i]
        )
        signups = max(0, round(expected_signups + rng.gauss(0, 18)))

        rows.append(
            {
                "DATE": dates[i].isoformat(),
                "signups": signups,
                "facebook_impressions": round(facebook_impressions[i]),
                "ppc_impressions": round(ppc_impressions[i]),
                "youtube_impressions": round(youtube_impressions[i]),
                "facebook_spend": round(facebook_spend[i], 2),
                "ppc_spend": round(ppc_spend[i], 2),
                "youtube_spend": round(youtube_spend[i], 2),
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} weekly rows to {OUT}")


if __name__ == "__main__":
    main()
