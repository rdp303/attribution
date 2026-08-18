from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from attribution import (
    ATTRIBUTION_SCENARIOS,
    BASELINE_SCENARIO,
    add_baseline_deltas,
    aggregate_by_scenario,
    campaign_comparison,
    scenario_label,
)
from meta_api import MetaAdsClient, MetaAPIError

ROOT = Path(__file__).resolve().parent
SAMPLE_PATH = ROOT / "data" / "sample_attribution.csv"

st.set_page_config(page_title="Meta Attribution Window Explorer", layout="wide")

st.title("Meta Attribution Window Explorer")
st.caption(
    "See how Meta campaign performance changes as the click/view attribution window changes."
)

with st.sidebar:
    st.header("Data")
    mode = st.radio("Source", ["Demo data", "Live Meta API"], index=0)

    conversion_action = st.text_input("Conversion action", value="purchase")

    if mode == "Demo data":
        raw = pd.read_csv(SAMPLE_PATH)
    else:
        token = st.text_input(
            "Access token",
            value=os.getenv("META_ACCESS_TOKEN", ""),
            type="password",
        )
        account_id = st.text_input(
            "Ad account ID",
            value=os.getenv("META_AD_ACCOUNT_ID", ""),
            help="Numeric ID; act_ prefix is optional.",
        )
        api_version = st.text_input(
            "Graph API version",
            value=os.getenv("META_API_VERSION", "v25.0"),
        )
        level = st.selectbox("Reporting level", ["campaign", "adset", "ad"], index=0)

        today = date.today()
        start_date = st.date_input("Start date", value=today - timedelta(days=30))
        end_date = st.date_input("End date", value=today)

        if st.button("Load Meta data", type="primary"):
            if not token or not account_id:
                st.error("Enter both an access token and ad account ID.")
                st.stop()
            try:
                client = MetaAdsClient(
                    access_token=token,
                    ad_account_id=account_id,
                    api_version=api_version,
                )
                raw = client.fetch_attribution_matrix(
                    since=start_date.isoformat(),
                    until=end_date.isoformat(),
                    level=level,
                    conversion_action=conversion_action,
                )
                st.session_state["meta_live_data"] = raw
            except MetaAPIError as exc:
                st.error(str(exc))
                st.stop()
        elif "meta_live_data" in st.session_state:
            raw = st.session_state["meta_live_data"]
        else:
            st.info("Enter credentials and click **Load Meta data**.")
            st.stop()

summary = add_baseline_deltas(aggregate_by_scenario(raw), BASELINE_SCENARIO)

available_scenarios = summary["scenario"].tolist()
selected = st.selectbox(
    "Attribution setting",
    available_scenarios,
    index=available_scenarios.index(BASELINE_SCENARIO)
    if BASELINE_SCENARIO in available_scenarios
    else 0,
    format_func=scenario_label,
)

selected_row = summary.loc[summary["scenario"] == selected].iloc[0]
baseline_row = summary.loc[summary["scenario"] == BASELINE_SCENARIO]
if baseline_row.empty:
    baseline_row = summary.iloc[[0]]
baseline_row = baseline_row.iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Attributed conversions",
    f"{selected_row['conversions']:,.0f}",
    f"{selected_row['conversions'] - baseline_row['conversions']:+,.0f} vs baseline",
)
c2.metric(
    "CPA",
    f"${selected_row['cpa']:,.2f}" if pd.notna(selected_row["cpa"]) else "—",
    (
        f"${selected_row['cpa'] - baseline_row['cpa']:+,.2f} vs baseline"
        if pd.notna(selected_row["cpa"]) and pd.notna(baseline_row["cpa"])
        else None
    ),
    delta_color="inverse",
)
c3.metric(
    "Attributed value",
    f"${selected_row['conversion_value']:,.0f}",
    f"${selected_row['conversion_value'] - baseline_row['conversion_value']:+,.0f} vs baseline",
)
c4.metric(
    "ROAS",
    f"{selected_row['roas']:.2f}x" if pd.notna(selected_row["roas"]) else "—",
    (
        f"{selected_row['roas'] - baseline_row['roas']:+.2f}x vs baseline"
        if pd.notna(selected_row["roas"]) and pd.notna(baseline_row["roas"])
        else None
    ),
)

st.divider()

left, right = st.columns([1.35, 1])

with left:
    st.subheader("Attribution sensitivity")
    metric = st.selectbox("Metric", ["roas", "cpa", "conversions"], index=0)
    chart_df = summary.sort_values(metric, ascending=(metric == "cpa"))
    fig = px.bar(
        chart_df,
        x="scenario_label",
        y=metric,
        hover_data=["conversions", "cpa", "conversion_value", "roas"],
        labels={"scenario_label": "Attribution window", metric: metric.upper()},
    )
    fig.update_layout(xaxis_tickangle=-55, height=470)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Click × view heatmap")
    heat_metric = st.selectbox(
        "Heatmap metric", ["roas", "cpa", "conversions"], index=0, key="heat_metric"
    )
    combos = summary.dropna(subset=["click_days", "view_days"])
    pivot = combos.pivot(index="view_days", columns="click_days", values=heat_metric)
    pivot = pivot.sort_index().sort_index(axis=1)
    heat = px.imshow(
        pivot,
        text_auto=".2f" if heat_metric != "conversions" else ".0f",
        aspect="auto",
        labels={"x": "Click window (days)", "y": "View window (days)", "color": heat_metric.upper()},
    )
    heat.update_layout(height=430)
    st.plotly_chart(heat, use_container_width=True)

st.subheader("Campaign sensitivity vs baseline")
campaigns = campaign_comparison(raw, selected, BASELINE_SCENARIO)
show_cols = [
    "entity_name",
    "spend_selected",
    "conversions_selected",
    "cpa_selected",
    "roas_selected",
    "conversion_delta_pct",
    "roas_delta_pct",
]
existing = [column for column in show_cols if column in campaigns.columns]
st.dataframe(campaigns[existing], use_container_width=True, hide_index=True)

st.subheader("All attribution scenarios")
display = summary[
    [
        "scenario_label",
        "spend",
        "conversions",
        "cpa",
        "conversion_value",
        "roas",
        "conversion_delta_pct",
        "roas_delta_pct",
    ]
].copy()
st.dataframe(display, use_container_width=True, hide_index=True)

st.download_button(
    "Download scenario comparison CSV",
    summary.to_csv(index=False).encode("utf-8"),
    file_name="meta_attribution_window_comparison.csv",
    mime="text/csv",
)

st.caption(
    "Attribution-window sensitivity is not incrementality. A longer window may increase reported credit without proving additional causal lift."
)
