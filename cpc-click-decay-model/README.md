# CPC Click Response / Decay Model

A lightweight paid-media response-curve project that estimates how **click volume changes as spend increases** for different campaign groups.

The core model is a power curve:

```text
clicks = k × spend^alpha
```

When `alpha < 1`, clicks still increase with spend, but at a decreasing rate. That lets the project quantify **click elasticity**, **average CPC**, and **marginal CPC** as budgets scale.

## Business questions

- Which campaign groups saturate fastest as spend grows?
- How much additional click volume should we expect from a 25%, 50%, or 100% spend increase?
- How quickly does marginal CPC deteriorate at higher budget levels?
- Which groups still have relatively efficient headroom?

## Grouping variable

The model is intentionally flexible. The grouping column can represent:

- campaign type
- brand vs. non-brand search
- market / geography
- product line
- audience
- keyword theme
- device

The included demo uses `campaign_group` with Brand Search, Non-Brand Search, and Competitor Search.

## Metrics

For each group, the model reports:

- `alpha_click_elasticity` — percent change in clicks associated with a 1% change in spend
- `decay_1_minus_alpha` — simple diminishing-returns score
- log-space R-squared
- predicted clicks at a reference spend level
- average CPC
- marginal CPC
- marginal clicks per additional $1,000 of spend

For the power curve, marginal CPC is derived from the slope of the fitted response curve rather than simply dividing spend by clicks.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The Streamlit app starts with synthetic demo data and also accepts CSV uploads.

## Expected input

At minimum:

```text
date
campaign_group
spend
clicks
```

Only the grouping, spend, and click columns are required by the model. The app lets you select the corresponding columns after upload.

## Project structure

```text
.
├── app.py
├── click_decay.py
├── generate_sample.py
├── requirements.txt
├── data/
│   └── sample_click_decay.csv
└── tests/
    └── test_click_decay.py
```

## Rebuild sample data

```bash
python generate_sample.py
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Interpretation

If a group has `alpha = 0.70`, a 10% increase in spend is associated with roughly a 7% increase in clicks. Because click volume grows more slowly than spend, both average and marginal CPC rise as the budget expands.

A lower alpha therefore indicates stronger observed saturation / click decay.

## Measurement note

This is a **descriptive response curve**, not a causal incrementality model. Spend is not randomly assigned: budget, bids, competition, search demand, query mix, seasonality, and platform optimization can all move spend and clicks together.

The model is most useful for exploratory planning and for visualizing diminishing-return behavior. Strong budget recommendations should be validated with experiments or a richer forecasting / causal framework.
