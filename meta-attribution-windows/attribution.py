from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import pandas as pd


CLICK_WINDOWS = ("1d_click", "7d_click", "28d_click")
VIEW_WINDOWS = ("1d_view", "7d_view", "28d_view")


@dataclass(frozen=True)
class AttributionScenario:
    click_window: str | None = None
    view_window: str | None = None

    @property
    def windows(self) -> tuple[str, ...]:
        return tuple(w for w in (self.click_window, self.view_window) if w)

    @property
    def key(self) -> str:
        return "+".join(self.windows)

    @property
    def label(self) -> str:
        parts: list[str] = []
        if self.click_window:
            parts.append(self.click_window.replace("_", " "))
        if self.view_window:
            parts.append(self.view_window.replace("_", " "))
        return " + ".join(parts)


def standard_scenarios(
    click_windows: Iterable[str] = CLICK_WINDOWS,
    view_windows: Iterable[str] = VIEW_WINDOWS,
    include_single_window: bool = True,
) -> list[AttributionScenario]:
    """Build the standard click/view attribution matrix."""
    clicks = tuple(click_windows)
    views = tuple(view_windows)
    scenarios: list[AttributionScenario] = []

    if include_single_window:
        scenarios.extend(AttributionScenario(click_window=w) for w in clicks)
        scenarios.extend(AttributionScenario(view_window=w) for w in views)

    scenarios.extend(
        AttributionScenario(click_window=click, view_window=view)
        for click, view in product(clicks, views)
    )
    return scenarios


def add_efficiency_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["cpa"] = out["spend"].div(out["conversions"].replace(0, pd.NA))
    out["roas"] = out["conversion_value"].div(out["spend"].replace(0, pd.NA))
    out["ctr"] = out["clicks"].div(out["impressions"].replace(0, pd.NA))
    return out


def aggregate_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["scenario_key", "scenario_label"], as_index=False)
        .agg(
            spend=("spend", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            conversion_value=("conversion_value", "sum"),
        )
    )
    return add_efficiency_metrics(grouped)


def campaign_comparison(df: pd.DataFrame, scenario_key: str, baseline_key: str) -> pd.DataFrame:
    selected = add_efficiency_metrics(df.loc[df["scenario_key"] == scenario_key].copy())
    baseline = add_efficiency_metrics(df.loc[df["scenario_key"] == baseline_key].copy())

    keep = [
        "entity_id",
        "entity_name",
        "spend",
        "impressions",
        "clicks",
        "conversions",
        "conversion_value",
        "cpa",
        "roas",
    ]
    selected = selected[keep]
    baseline = baseline[["entity_id", "conversions", "cpa", "roas"]].rename(
        columns={
            "conversions": "baseline_conversions",
            "cpa": "baseline_cpa",
            "roas": "baseline_roas",
        }
    )
    merged = selected.merge(baseline, on="entity_id", how="left")
    merged["conversion_delta"] = merged["conversions"] - merged["baseline_conversions"]
    merged["cpa_pct_vs_baseline"] = merged["cpa"].div(merged["baseline_cpa"]) - 1
    merged["roas_pct_vs_baseline"] = merged["roas"].div(merged["baseline_roas"]) - 1
    return merged.sort_values("spend", ascending=False)


def attribution_matrix(summary: pd.DataFrame, metric: str) -> pd.DataFrame:
    paired = summary[summary["scenario_key"].str.contains("+", regex=False)].copy()
    paired[["click_window", "view_window"]] = paired["scenario_key"].str.split(
        "+", n=1, expand=True, regex=False
    )
    matrix = paired.pivot(index="click_window", columns="view_window", values=metric)
    click_order = [w for w in CLICK_WINDOWS if w in matrix.index]
    view_order = [w for w in VIEW_WINDOWS if w in matrix.columns]
    return matrix.reindex(index=click_order, columns=view_order)
