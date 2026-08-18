from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from attribution import (
    CLICK_WINDOWS,
    VIEW_WINDOWS,
    add_efficiency_metrics,
    aggregate_scenarios,
    attribution_matrix,
    campaign_comparison,
    standard_scenarios,
)
from meta_api import MetaAPIError, MetaReportConfig, fetch_all_scenarios


st.set_page_config(page_title="Meta Attribution Window Explorer", page_icon="📈", layout="wide")
st.title("Meta Attribution Window Explorer")
st.caption(
    "See how campaign performance changes when the same Meta Ads results are reported "
    "under different click/view attribution-window combinations."
)


@st.cache_data(show_spinner=False)
def load_sample() -> pd.DataFrame:
    return pd.read_csv("data/sample_attribution.csv")


@st.cache_data(show_spinner=True, ttl=900)
def load_live(
    account_id: str,
    access_token: str,
    since: str,
    until: str,
    level: str,
    action_type: str,
    api_version: str,
    include_28d: bool,
) -> pd.DataFrame:
    clicks = CLICK_WINDOWS if include_28d else CLICK_WINDOWS[:2]
    views = VIEW_WINDOWS if include_28d else VIEW_WINDOWS[:2]
    config = MetaReportConfig(
        account_id=account_id,
        access_token=access_token,
        since=since,
        until=until,
        level=level,
        action_type=action_type,
        api_version=api_version,
    )
    return fetch_all_scenarios(config, standard_scenarios(clicks, views))


with st.sidebar:
    st.header("Report settings")
    source = st.radio("Data source", ["Demo data", "Live Meta API"])
    include_28d = st.checkbox("Include 28-day windows", value=True)

    if source == "Live Meta API":
        account_id = st.text_input("Ad account ID", value=os.getenv("META_AD_ACCOUNT_ID", ""))
        access_token = st.text_input(
            "Access token", value=os.getenv("META_ACCESS_TOKEN", ""), type="password"
        )
        api_version = st.text_input(
            "Graph API version", value=os.getenv("META_API_VERSION", "v25.0")
        )
        level = st.selectbox("Reporting level", ["campaign", "adset", "ad"])
        action_type = st.text_input("Conversion action type", value="purchase")
        default_until = date.today() - timedelta(days=1)
        default_since = default_until - timedelta(days=29)
        since = st.date_input("Since", value=default_since)
        until = st.date_input("Until", value=default_until)
        run_live = st.button("Pull Meta data", type="primary", use_container_width=True)
    else:
        run_live = False


if source == "Demo data":
    df = load_sample()
    if not include_28d:
        df = df[~df["scenario_key"].str.contains("28d")].copy()
else:
    if not run_live:
        st.info("Enter Meta credentials in the sidebar and click **Pull Meta data**.")
        st.stop()
    if not account_id or not access_token:
        st.error("Ad account ID and access token are required.")
        st.stop()
    try:
        df = load_live(
            account_id,
            access_token,
            str(since),
            str(until),
            level,
            action_type,
            api_version,
            include_28d,
        )
    except MetaAPIError as exc:
        st.error(str(exc))
        st.stop()

if df.empty:
    st.warning("No rows were returned for the selected period/settings.")
    st.stop()

summary = aggregate_scenarios(df)
scenario_options = dict(zip(summary["scenario_label"], summary["scenario_key"]))
labels = list(scenario_options)
preferred_baseline = "7d click + 1d view"
baseline_default = preferred_baseline if preferred_baseline in labels else labels[0]

c1, c2 = st.columns(2)
with c1:
    selected_label = st.selectbox(
        "Selected attribution setting", labels, index=labels.index(baseline_default)
    )
with c2:
    baseline_label = st.selectbox(
        "Comparison baseline", labels, index=labels.index(baseline_default)
    )

selected_key = scenario_options[selected_label]
baseline_key = scenario_options[baseline_label]
selected_summary = add_efficiency_metrics(df[df["scenario_key"] == selected_key])
baseline_summary = add_efficiency_metrics(df[df["scenario_key"] == baseline_key])

spend = selected_summary["spend"].sum()
conversions = selected_summary["conversions"].sum()
value = selected_summary["conversion_value"].sum()
cpa = spend / conversions if conversions else 0
roas = value / spend if spend else 0
base_conversions = baseline_summary["conversions"].sum()
base_spend = baseline_summary["spend"].sum()
base_cpa = base_spend / base_conversions if base_conversions else 0
base_roas = baseline_summary["conversion_value"].sum() / base_spend if base_spend else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Spend", f"${spend:,.0f}")
m2.metric(
    "Conversions",
    f"{conversions:,.1f}",
    f"{(conversions / base_conversions - 1):+.1%}" if base_conversions else None,
)
m3.metric(
    "CPA",
    f"${cpa:,.2f}",
    f"{(cpa / base_cpa - 1):+.1%}" if base_cpa else None,
    delta_color="inverse",
)
m4.metric(
    "ROAS",
    f"{roas:.2f}x",
    f"{(roas / base_roas - 1):+.1%}" if base_roas else None,
)

st.divider()
left, right = st.columns([1.2, 1])

with left:
    st.subheader("Attribution sensitivity")
    chart_metric = st.selectbox(
        "Metric", ["conversions", "cpa", "roas", "conversion_value"], index=2
    )
    chart_df = summary.sort_values(chart_metric, ascending=False)
    fig = px.bar(
        chart_df,
        x="scenario_label",
        y=chart_metric,
        hover_data=["spend", "conversions", "cpa", "roas"],
        labels={
            "scenario_label": "Attribution setting",
            chart_metric: chart_metric.replace("_", " ").title(),
        },
    )
    fig.update_layout(xaxis_tickangle=-45, height=480, margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Click × view matrix")
    matrix_metric = st.selectbox("Matrix metric", ["roas", "cpa", "conversions"], index=0)
    matrix = attribution_matrix(summary, matrix_metric)
    fig2 = px.imshow(
        matrix,
        text_auto=".2f",
        aspect="auto",
        labels={"x": "View window", "y": "Click window", "color": matrix_metric.upper()},
    )
    fig2.update_layout(height=480, margin=dict(t=20))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Campaign-level impact")
campaigns = campaign_comparison(df, selected_key, baseline_key)
display = campaigns.rename(
    columns={
        "entity_name": "Campaign",
        "spend": "Spend",
        "impressions": "Impressions",
        "clicks": "Clicks",
        "conversions": "Conversions",
        "conversion_value": "Revenue",
        "cpa": "CPA",
        "roas": "ROAS",
        "conversion_delta": "Conversion Δ",
        "cpa_pct_vs_baseline": "CPA % vs baseline",
        "roas_pct_vs_baseline": "ROAS % vs baseline",
    }
)
st.dataframe(
    display[
        [
            "Campaign",
            "Spend",
            "Conversions",
            "Conversion Δ",
            "Revenue",
            "CPA",
            "CPA % vs baseline",
            "ROAS",
            "ROAS % vs baseline",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Spend": st.column_config.NumberColumn(format="$%.0f"),
        "Revenue": st.column_config.NumberColumn(format="$%.0f"),
        "CPA": st.column_config.NumberColumn(format="$%.2f"),
        "ROAS": st.column_config.NumberColumn(format="%.2fx"),
        "CPA % vs baseline": st.column_config.NumberColumn(format="%.1%%"),
        "ROAS % vs baseline": st.column_config.NumberColumn(format="%.1%%"),
    },
)

st.subheader("All attribution settings")
scenario_table = summary[
    ["scenario_label", "spend", "conversions", "conversion_value", "cpa", "roas"]
].copy()
scenario_table.columns = ["Attribution setting", "Spend", "Conversions", "Revenue", "CPA", "ROAS"]
st.dataframe(
    scenario_table.sort_values("ROAS", ascending=False),
    hide_index=True,
    use_container_width=True,
    column_config={
        "Spend": st.column_config.NumberColumn(format="$%.0f"),
        "Revenue": st.column_config.NumberColumn(format="$%.0f"),
        "CPA": st.column_config.NumberColumn(format="$%.2f"),
        "ROAS": st.column_config.NumberColumn(format="%.2fx"),
    },
)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download normalized attribution data", csv, "meta_attribution_windows.csv", "text/csv"
)

st.caption(
    "Attribution windows change how Meta credits conversions; they do not change spend, "
    "impressions, or clicks. Use this report to understand measurement sensitivity, not to infer incrementality."
)
