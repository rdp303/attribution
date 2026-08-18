from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd
import requests

from attribution import AttributionScenario


DEFAULT_API_VERSION = os.getenv("META_API_VERSION", "v25.0")
GRAPH_ROOT = "https://graph.facebook.com"


class MetaAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class MetaReportConfig:
    account_id: str
    access_token: str
    since: str
    until: str
    level: str = "campaign"
    action_type: str = "purchase"
    action_report_time: str = "conversion"
    api_version: str = DEFAULT_API_VERSION


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def extract_action_metric(
    rows: list[dict[str, Any]] | None,
    action_type: str,
    windows: Iterable[str],
) -> float:
    """Extract one action metric without summing potentially overlapping windows."""
    if not rows:
        return 0.0

    match = next((row for row in rows if row.get("action_type") == action_type), None)
    if not match:
        return 0.0

    if "value" in match:
        return _as_float(match.get("value"))

    windows = tuple(windows)
    if len(windows) == 1 and windows[0] in match:
        return _as_float(match.get(windows[0]))

    raise MetaAPIError(
        "Meta returned attribution-window fields without a combined 'value'. "
        "The report will not sum overlapping windows because that can double-count conversions."
    )


def _entity_fields(level: str) -> tuple[str, str]:
    mapping = {
        "campaign": ("campaign_id", "campaign_name"),
        "adset": ("adset_id", "adset_name"),
        "ad": ("ad_id", "ad_name"),
    }
    if level not in mapping:
        raise ValueError(f"Unsupported level: {level}")
    return mapping[level]


def fetch_scenario(config: MetaReportConfig, scenario: AttributionScenario) -> pd.DataFrame:
    entity_id_field, entity_name_field = _entity_fields(config.level)
    account_id = config.account_id.replace("act_", "")
    url = f"{GRAPH_ROOT}/{config.api_version}/act_{account_id}/insights"

    params = {
        "access_token": config.access_token,
        "level": config.level,
        "fields": ",".join(
            [
                entity_id_field,
                entity_name_field,
                "spend",
                "impressions",
                "clicks",
                "actions",
                "action_values",
            ]
        ),
        "time_range": json.dumps({"since": config.since, "until": config.until}),
        "action_attribution_windows": json.dumps(list(scenario.windows)),
        "action_report_time": config.action_report_time,
        "use_unified_attribution_setting": "false",
        "limit": 500,
    }

    records: list[dict[str, Any]] = []
    next_url: str | None = url
    next_params: dict[str, Any] | None = params

    while next_url:
        response = requests.get(next_url, params=next_params, timeout=60)
        try:
            payload = response.json()
        except ValueError as exc:
            raise MetaAPIError(f"Meta returned a non-JSON response ({response.status_code}).") from exc

        if response.status_code >= 400 or "error" in payload:
            error = payload.get("error", {})
            message = error.get("message", response.text)
            raise MetaAPIError(f"Meta API error: {message}")

        for row in payload.get("data", []):
            records.append(
                {
                    "entity_id": str(row.get(entity_id_field, "")),
                    "entity_name": row.get(entity_name_field, "(unnamed)"),
                    "scenario_key": scenario.key,
                    "scenario_label": scenario.label,
                    "spend": _as_float(row.get("spend")),
                    "impressions": _as_float(row.get("impressions")),
                    "clicks": _as_float(row.get("clicks")),
                    "conversions": extract_action_metric(
                        row.get("actions"), config.action_type, scenario.windows
                    ),
                    "conversion_value": extract_action_metric(
                        row.get("action_values"), config.action_type, scenario.windows
                    ),
                }
            )

        next_url = payload.get("paging", {}).get("next")
        next_params = None

    return pd.DataFrame.from_records(records)


def fetch_all_scenarios(
    config: MetaReportConfig,
    scenarios: Iterable[AttributionScenario],
) -> pd.DataFrame:
    frames = [fetch_scenario(config, scenario) for scenario in scenarios]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
