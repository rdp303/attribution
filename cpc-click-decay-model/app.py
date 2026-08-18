from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from click_decay import curve_summary, fit_by_group, scenario_table

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / "data" / "sample_click_decay.csv"

st.set_page_config(page_title="CPC Click Decay Model", layout="wide")
st.title("CPC Click Response / Decay Model")
st.caption(
    "Model diminishing click returns as spend rises, separately by campaign or another grouping variable."
)

with st.sidebar:
    st.header("Data")
    source = st.radio("Source", ["Demo data", "Upload CSV"])
    if source == "Demo data":
        df = pd.read_csv(SAMPLE)
    else:
        uploaded = st.file_uploader("CSV", type="csv")
        if uploaded is None:
            st.info("Upload a CSV to continue.")
            st.stop()
        df = pd.read_csv(uploaded)

    cols = df.columns.tolist()
    group_col = st.selectbox("Grouping column", cols, index=cols.index("campaign_group") if "campaign_group" in cols else 0)
    spend_col = st.selectbox("Spend column", cols, index=cols.index("spend") if "spend" in cols else 0)
    clicks_col = st.selectbox("Clicks column", cols, index=cols.index("clicks") if "clicks" in cols else 0)
    min_obs = st.number_input("Minimum observations per group", min_value=5, max_value=100, value=12)

curves = fit_by_group(df, group_col, spend_col, clicks_col, int(min_obs))
if not curves:
    st.error("No groups have enough positive spend/click observations to fit a model.")
    st.stop()

summary = curve_summary(curves.values())

c1, c2, c3 = st.columns(3)
c1.metric("Groups modeled", f"{len(curves)}")
c2.metric("Median click elasticity", f"{summary['alpha_click_elasticity'].median():.2f}")
c3.metric("Median decay", f"{summary['decay_1_minus_alpha'].median():.2f}")

st.markdown(
    "**Interpretation:** an elasticity (`alpha`) below 1 means diminishing returns. "
    "For example, `alpha = 0.70` implies a 10% increase in spend is associated with roughly a 7% increase in clicks."
)

st.subheader("Observed spend vs. clicks with fitted response curves")
fig = px.scatter(df, x=spend_col, y=clicks_col, color=group_col, opacity=0.55)
for group, curve in curves.items():
    grid = np.geomspace(curve.min_spend, curve.max_spend, 100)
    fig.add_trace(
        go.Scatter(
            x=grid,
            y=curve.predict_clicks(grid),
            mode="lines",
            name=f"{group} fitted",
            showlegend=True,
        )
    )
fig.update_layout(height=520, xaxis_title="Spend", yaxis_title="Clicks")
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Group model diagnostics")
    display = summary.copy()
    display["alpha_click_elasticity"] = display["alpha_click_elasticity"].round(3)
    display["decay_1_minus_alpha"] = display["decay_1_minus_alpha"].round(3)
    display["r_squared_log_space"] = display["r_squared_log_space"].round(3)
    display["average_cpc"] = display["average_cpc"].round(2)
    display["marginal_cpc"] = display["marginal_cpc"].round(2)
    st.dataframe(display, hide_index=True, use_container_width=True)

with right:
    st.subheader("CPC deterioration as spend rises")
    scenarios = scenario_table(curves.values())
    metric = st.selectbox("Metric", ["average_cpc", "marginal_cpc"], index=1)
    line = px.line(
        scenarios,
        x="spend_multiplier",
        y=metric,
        color="group",
        markers=True,
        labels={"spend_multiplier": "Spend vs reference", metric: metric.replace("_", " ").title()},
    )
    line.update_layout(height=430)
    st.plotly_chart(line, use_container_width=True)

st.subheader("Spend scenarios")
st.dataframe(
    scenarios.assign(
        spend=lambda x: x["spend"].round(0),
        predicted_clicks=lambda x: x["predicted_clicks"].round(0),
        average_cpc=lambda x: x["average_cpc"].round(2),
        marginal_cpc=lambda x: x["marginal_cpc"].round(2),
        marginal_clicks_per_1000=lambda x: x["marginal_clicks_per_1000"].round(1),
    ),
    hide_index=True,
    use_container_width=True,
)

st.download_button(
    "Download scenario table",
    scenarios.to_csv(index=False).encode("utf-8"),
    file_name="cpc_click_decay_scenarios.csv",
    mime="text/csv",
)

st.caption(
    "This is a descriptive response-curve model, not a causal incrementality estimate. "
    "Budget, bids, competition, query mix, seasonality, and platform optimization can all affect the observed spend-click relationship."
)
