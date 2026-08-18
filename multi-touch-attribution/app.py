from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from generate_sample import generate as generate_sample
from attribution_models import (
    MODEL_NAMES,
    channel_summary,
    compare_models,
    journey_level_metrics,
    journey_paths,
    model_share_matrix,
    model_volatility,
    validate_touchpoints,
)

MODEL_LABELS = {
    "first_touch": "First touch",
    "last_touch": "Last touch",
    "linear": "Linear",
    "time_decay": "Time decay",
    "position_based": "Position based (40/20/40)",
}

st.set_page_config(page_title="Multi-Touch Attribution Playground", layout="wide")
st.title("Multi-Touch Attribution Playground")
st.caption(
    "See how the same conversion journeys allocate channel credit differently under common rule-based attribution models."
)

with st.sidebar:
    st.header("Data")
    source = st.radio("Source", ["Demo data", "Upload CSV"], index=0)

    if source == "Demo data":
        raw = generate_sample(n_journeys=600)
    else:
        uploaded = st.file_uploader("Touchpoint CSV", type=["csv"])
        if uploaded is None:
            st.info("Upload a CSV to continue.")
            st.stop()
        raw = pd.read_csv(uploaded)

    st.header("Model")
    selected_model = st.selectbox(
        "Attribution model",
        MODEL_NAMES,
        index=3,
        format_func=lambda x: MODEL_LABELS[x],
    )
    half_life_days = st.slider(
        "Time-decay half-life (days)",
        min_value=1.0,
        max_value=30.0,
        value=7.0,
        step=1.0,
        disabled=selected_model != "time_decay",
        help="A touch this many days before conversion receives half the weight of an otherwise identical touch at conversion.",
    )

try:
    data = validate_touchpoints(raw)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

metrics = journey_level_metrics(data)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Journeys", f"{metrics['journeys']:,.0f}")
c2.metric("Conversions", f"{metrics['conversions']:,.0f}")
c3.metric("Journey conversion rate", f"{metrics['conversion_rate']:.1%}")
c4.metric("Avg touches to convert", f"{metrics['avg_touches_to_convert']:.1f}")

st.divider()

summary = channel_summary(data, selected_model, half_life_days)

left, right = st.columns([1.25, 1])

with left:
    st.subheader(f"Channel credit — {MODEL_LABELS[selected_model]}")
    fig = px.bar(
        summary,
        x="channel",
        y="conversion_credit",
        hover_data=["conversion_share", "revenue_credit", "revenue_share"],
        labels={
            "channel": "Channel",
            "conversion_credit": "Attributed conversions",
        },
    )
    fig.update_layout(height=430)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Model sensitivity")
    matrix = model_share_matrix(data, half_life_days)
    heat = px.imshow(
        matrix,
        text_auto=".1%",
        aspect="auto",
        labels={
            "x": "Attribution model",
            "y": "Channel",
            "color": "Conversion share",
        },
    )
    heat.update_xaxes(
        ticktext=[MODEL_LABELS.get(x, x) for x in matrix.columns],
        tickvals=list(matrix.columns),
    )
    heat.update_layout(height=430)
    st.plotly_chart(heat, use_container_width=True)

st.subheader("Which channels are most sensitive to the attribution rule?")
volatility = model_volatility(data, half_life_days)
vol_display = volatility.copy()
for col in ["min_share", "max_share", "share_range"]:
    vol_display[col] = vol_display[col].map(lambda x: f"{x:.1%}")
st.dataframe(vol_display, use_container_width=True, hide_index=True)

st.subheader("Side-by-side model comparison")
comparison = compare_models(data, half_life_days)
comparison["model_label"] = comparison["model"].map(MODEL_LABELS)
table = comparison.pivot_table(
    index="channel",
    columns="model_label",
    values="conversion_credit",
    fill_value=0,
)
st.dataframe(table.round(1), use_container_width=True)

st.subheader("Common customer paths")
paths = journey_paths(data, converted_only=False).head(15)
path_display = paths.copy()
path_display["conversion_rate"] = path_display["conversion_rate"].map(lambda x: f"{x:.1%}")
path_display["revenue"] = path_display["revenue"].map(lambda x: f"${x:,.0f}")
st.dataframe(path_display, use_container_width=True, hide_index=True)

st.download_button(
    "Download channel attribution CSV",
    comparison.to_csv(index=False).encode("utf-8"),
    file_name="multi_touch_attribution_comparison.csv",
    mime="text/csv",
)

with st.expander("How the models assign credit"):
    st.markdown(
        """
- **First touch:** 100% of credit goes to the first observed channel.
- **Last touch:** 100% goes to the final channel before conversion.
- **Linear:** every touch in the journey receives equal credit.
- **Time decay:** later touches receive exponentially more credit; the half-life is configurable.
- **Position based:** 40% to the first touch, 40% to the last touch, and 20% split across the middle touches.

These are attribution rules, not causal estimates. They answer **how credit changes under different allocation assumptions**, not whether a channel caused the conversion.
"""
    )
