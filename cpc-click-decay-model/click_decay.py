from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PowerCurve:
    group: str
    intercept_log: float
    alpha: float
    r_squared: float
    n_obs: int
    min_spend: float
    max_spend: float

    @property
    def k(self) -> float:
        return float(np.exp(self.intercept_log))

    @property
    def decay(self) -> float:
        """Convenience measure: 0 means linear; larger values mean stronger diminishing returns."""
        return 1.0 - self.alpha

    def predict_clicks(self, spend: float | np.ndarray) -> float | np.ndarray:
        spend_arr = np.asarray(spend, dtype=float)
        result = self.k * np.power(spend_arr, self.alpha)
        return float(result) if np.ndim(spend) == 0 else result

    def average_cpc(self, spend: float | np.ndarray) -> float | np.ndarray:
        clicks = self.predict_clicks(spend)
        return np.asarray(spend, dtype=float) / clicks

    def marginal_clicks_per_dollar(self, spend: float | np.ndarray) -> float | np.ndarray:
        spend_arr = np.asarray(spend, dtype=float)
        result = self.alpha * self.k * np.power(spend_arr, self.alpha - 1.0)
        return float(result) if np.ndim(spend) == 0 else result

    def marginal_cpc(self, spend: float | np.ndarray) -> float | np.ndarray:
        marginal_clicks = self.marginal_clicks_per_dollar(spend)
        return 1.0 / marginal_clicks


def _clean_group(df: pd.DataFrame, spend_col: str, clicks_col: str) -> pd.DataFrame:
    out = df[[spend_col, clicks_col]].copy()
    out[spend_col] = pd.to_numeric(out[spend_col], errors="coerce")
    out[clicks_col] = pd.to_numeric(out[clicks_col], errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    return out[(out[spend_col] > 0) & (out[clicks_col] > 0)]


def fit_power_curve(
    df: pd.DataFrame,
    spend_col: str,
    clicks_col: str,
    group_name: str = "all",
    min_observations: int = 8,
) -> PowerCurve:
    """Fit clicks = k * spend^alpha with OLS in log-log space."""
    clean = _clean_group(df, spend_col, clicks_col)
    if len(clean) < min_observations:
        raise ValueError(
            f"Group '{group_name}' has {len(clean)} usable observations; "
            f"at least {min_observations} are required."
        )

    x = np.log(clean[spend_col].to_numpy(dtype=float))
    y = np.log(clean[clicks_col].to_numpy(dtype=float))

    alpha, intercept = np.polyfit(x, y, deg=1)
    fitted = intercept + alpha * x
    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    return PowerCurve(
        group=str(group_name),
        intercept_log=float(intercept),
        alpha=float(alpha),
        r_squared=float(r_squared),
        n_obs=int(len(clean)),
        min_spend=float(clean[spend_col].min()),
        max_spend=float(clean[spend_col].max()),
    )


def fit_by_group(
    df: pd.DataFrame,
    group_col: str,
    spend_col: str,
    clicks_col: str,
    min_observations: int = 8,
) -> dict[str, PowerCurve]:
    curves: dict[str, PowerCurve] = {}
    for group, group_df in df.groupby(group_col, dropna=False):
        name = str(group)
        try:
            curves[name] = fit_power_curve(
                group_df,
                spend_col=spend_col,
                clicks_col=clicks_col,
                group_name=name,
                min_observations=min_observations,
            )
        except ValueError:
            continue
    return curves


def curve_summary(curves: Iterable[PowerCurve]) -> pd.DataFrame:
    rows = []
    for curve in curves:
        reference_spend = float(np.sqrt(curve.min_spend * curve.max_spend))
        predicted_clicks = float(curve.predict_clicks(reference_spend))
        rows.append(
            {
                "group": curve.group,
                "alpha_click_elasticity": curve.alpha,
                "decay_1_minus_alpha": curve.decay,
                "r_squared_log_space": curve.r_squared,
                "observations": curve.n_obs,
                "reference_spend": reference_spend,
                "predicted_clicks": predicted_clicks,
                "average_cpc": float(curve.average_cpc(reference_spend)),
                "marginal_cpc": float(curve.marginal_cpc(reference_spend)),
            }
        )
    return pd.DataFrame(rows).sort_values("group").reset_index(drop=True)


def scenario_table(
    curves: Iterable[PowerCurve],
    multipliers: Iterable[float] = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0),
) -> pd.DataFrame:
    rows = []
    for curve in curves:
        baseline = float(np.sqrt(curve.min_spend * curve.max_spend))
        for multiplier in multipliers:
            spend = baseline * float(multiplier)
            clicks = float(curve.predict_clicks(spend))
            rows.append(
                {
                    "group": curve.group,
                    "spend_multiplier": float(multiplier),
                    "spend": spend,
                    "predicted_clicks": clicks,
                    "average_cpc": spend / clicks,
                    "marginal_cpc": float(curve.marginal_cpc(spend)),
                    "marginal_clicks_per_1000": float(curve.marginal_clicks_per_dollar(spend)) * 1000,
                }
            )
    return pd.DataFrame(rows)
