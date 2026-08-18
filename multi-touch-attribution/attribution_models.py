from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "journey_id",
    "touch_time",
    "channel",
    "converted",
    "conversion_value",
}

MODEL_NAMES = (
    "first_touch",
    "last_touch",
    "linear",
    "time_decay",
    "position_based",
)


def validate_touchpoints(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize a touchpoint-level journey dataset."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    out = df.copy()
    out["touch_time"] = pd.to_datetime(out["touch_time"], errors="coerce", utc=True)
    if out["touch_time"].isna().any():
        raise ValueError("touch_time contains invalid timestamps")

    out["converted"] = pd.to_numeric(out["converted"], errors="coerce").fillna(0).astype(int)
    out["conversion_value"] = pd.to_numeric(
        out["conversion_value"], errors="coerce"
    ).fillna(0.0)

    if not out["converted"].isin([0, 1]).all():
        raise ValueError("converted must contain only 0/1 values")
    if (out["conversion_value"] < 0).any():
        raise ValueError("conversion_value cannot be negative")
    if out["journey_id"].isna().any() or out["channel"].isna().any():
        raise ValueError("journey_id and channel cannot be null")

    out["journey_id"] = out["journey_id"].astype(str)
    out["channel"] = out["channel"].astype(str)
    return out.sort_values(["journey_id", "touch_time"]).reset_index(drop=True)


def _position_weights(n_touches: int) -> np.ndarray:
    if n_touches <= 0:
        raise ValueError("n_touches must be positive")
    if n_touches == 1:
        return np.array([1.0])
    if n_touches == 2:
        return np.array([0.5, 0.5])

    weights = np.full(n_touches, 0.20 / (n_touches - 2))
    weights[0] = 0.40
    weights[-1] = 0.40
    return weights


def _time_decay_weights(times: pd.Series, half_life_days: float) -> np.ndarray:
    if half_life_days <= 0:
        raise ValueError("half_life_days must be greater than zero")

    conversion_time = times.iloc[-1]
    days_before = (conversion_time - times).dt.total_seconds().to_numpy() / 86400.0
    raw = np.power(0.5, days_before / half_life_days)
    return raw / raw.sum()


def _weights_for_journey(
    journey: pd.DataFrame,
    model: str,
    half_life_days: float,
) -> np.ndarray:
    n = len(journey)
    if model == "first_touch":
        weights = np.zeros(n)
        weights[0] = 1.0
        return weights
    if model == "last_touch":
        weights = np.zeros(n)
        weights[-1] = 1.0
        return weights
    if model == "linear":
        return np.full(n, 1.0 / n)
    if model == "time_decay":
        return _time_decay_weights(journey["touch_time"], half_life_days)
    if model == "position_based":
        return _position_weights(n)
    raise ValueError(f"Unknown attribution model: {model}")


def attribute_conversions(
    df: pd.DataFrame,
    model: str,
    half_life_days: float = 7.0,
) -> pd.DataFrame:
    """Assign conversion and revenue credit to touchpoints in converted journeys."""
    if model not in MODEL_NAMES:
        raise ValueError(f"model must be one of: {', '.join(MODEL_NAMES)}")

    touchpoints = validate_touchpoints(df)
    credited_rows: list[pd.DataFrame] = []

    for _, journey in touchpoints.groupby("journey_id", sort=False):
        converted = int(journey["converted"].max())
        if not converted:
            continue

        conversion_value = float(journey["conversion_value"].sum())
        weights = _weights_for_journey(journey, model, half_life_days)

        credited = journey.copy()
        credited["model"] = model
        credited["weight"] = weights
        credited["conversion_credit"] = weights
        credited["revenue_credit"] = weights * conversion_value
        credited_rows.append(credited)

    if not credited_rows:
        return pd.DataFrame(
            columns=list(touchpoints.columns)
            + ["model", "weight", "conversion_credit", "revenue_credit"]
        )

    return pd.concat(credited_rows, ignore_index=True)


def channel_summary(
    df: pd.DataFrame,
    model: str,
    half_life_days: float = 7.0,
) -> pd.DataFrame:
    """Aggregate attributed conversion/revenue credit to channel."""
    credited = attribute_conversions(df, model, half_life_days)
    if credited.empty:
        return pd.DataFrame(
            columns=[
                "channel",
                "conversion_credit",
                "revenue_credit",
                "conversion_share",
                "revenue_share",
            ]
        )

    summary = (
        credited.groupby("channel", as_index=False)
        .agg(
            conversion_credit=("conversion_credit", "sum"),
            revenue_credit=("revenue_credit", "sum"),
        )
        .sort_values("conversion_credit", ascending=False)
    )
    total_conv = summary["conversion_credit"].sum()
    total_rev = summary["revenue_credit"].sum()
    summary["conversion_share"] = (
        summary["conversion_credit"] / total_conv if total_conv else 0.0
    )
    summary["revenue_share"] = (
        summary["revenue_credit"] / total_rev if total_rev else 0.0
    )
    return summary.reset_index(drop=True)


def compare_models(
    df: pd.DataFrame,
    half_life_days: float = 7.0,
) -> pd.DataFrame:
    """Return channel-level conversion credit for every supported model."""
    frames = []
    for model in MODEL_NAMES:
        summary = channel_summary(df, model, half_life_days)
        summary["model"] = model
        frames.append(summary)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def model_share_matrix(
    df: pd.DataFrame,
    half_life_days: float = 7.0,
) -> pd.DataFrame:
    comparison = compare_models(df, half_life_days)
    if comparison.empty:
        return pd.DataFrame()
    return (
        comparison.pivot(
            index="channel",
            columns="model",
            values="conversion_share",
        )
        .fillna(0.0)
        .sort_index()
    )


def model_volatility(
    df: pd.DataFrame,
    half_life_days: float = 7.0,
) -> pd.DataFrame:
    """Rank channels by how much their conversion share changes across models."""
    matrix = model_share_matrix(df, half_life_days)
    if matrix.empty:
        return pd.DataFrame(columns=["channel", "min_share", "max_share", "share_range"])

    result = pd.DataFrame(
        {
            "channel": matrix.index,
            "min_share": matrix.min(axis=1).values,
            "max_share": matrix.max(axis=1).values,
        }
    )
    result["share_range"] = result["max_share"] - result["min_share"]
    return result.sort_values("share_range", ascending=False).reset_index(drop=True)


def journey_paths(df: pd.DataFrame, converted_only: bool = True) -> pd.DataFrame:
    """Summarize the most common ordered channel paths."""
    touchpoints = validate_touchpoints(df)

    rows = []
    for journey_id, journey in touchpoints.groupby("journey_id", sort=False):
        converted = int(journey["converted"].max())
        if converted_only and not converted:
            continue
        rows.append(
            {
                "journey_id": journey_id,
                "path": " → ".join(journey["channel"].tolist()),
                "touches": len(journey),
                "converted": converted,
                "conversion_value": float(journey["conversion_value"].sum()),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=["path", "journeys", "conversions", "conversion_rate", "revenue"]
        )

    paths = pd.DataFrame(rows)
    summary = (
        paths.groupby("path", as_index=False)
        .agg(
            journeys=("journey_id", "nunique"),
            conversions=("converted", "sum"),
            revenue=("conversion_value", "sum"),
            avg_touches=("touches", "mean"),
        )
        .sort_values(["conversions", "journeys"], ascending=False)
    )
    summary["conversion_rate"] = summary["conversions"] / summary["journeys"]
    return summary.reset_index(drop=True)


def journey_level_metrics(df: pd.DataFrame) -> dict[str, float]:
    touchpoints = validate_touchpoints(df)
    grouped = touchpoints.groupby("journey_id", sort=False)
    journeys = grouped.agg(
        converted=("converted", "max"),
        conversion_value=("conversion_value", "sum"),
        touches=("channel", "size"),
    )

    converted = journeys[journeys["converted"] == 1]
    return {
        "journeys": float(len(journeys)),
        "conversions": float(converted["converted"].sum()),
        "conversion_rate": float(journeys["converted"].mean()) if len(journeys) else 0.0,
        "revenue": float(converted["conversion_value"].sum()),
        "avg_touches_to_convert": float(converted["touches"].mean()) if len(converted) else 0.0,
    }
