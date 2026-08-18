# Multi-Touch Attribution Playground

An interactive Python/Streamlit project for comparing common **rule-based multi-touch attribution models** on the exact same customer journeys.

The point of the project is not to declare one attribution rule "correct." It is to make the modeling assumption visible by showing how channel credit changes when the rule changes.

## What it answers

- How much credit does each channel receive under first-touch vs. last-touch attribution?
- Which channels benefit most from time-decay or position-based models?
- Which channels are most sensitive to the attribution rule?
- What are the most common converting paths?
- How different can channel-level conversion credit look even though the underlying journeys never changed?

## Included models

```text
First touch
Last touch
Linear
Time decay
Position based (40 / 20 / 40)
```

### First touch

100% of the conversion goes to the first observed channel in the journey.

### Last touch

100% goes to the final observed channel before conversion.

### Linear

Every touch receives equal credit.

### Time decay

Later interactions receive more credit using exponential decay:

```text
weight ∝ 0.5 ^ (days_before_conversion / half_life_days)
```

The Streamlit report lets the user change the half-life.

### Position based

For journeys with three or more touches:

```text
40% → first touch
20% → split across middle touches
40% → last touch
```

One-touch journeys receive 100% on that touch; two-touch journeys split 50/50.

## Data format

One row per touchpoint:

```text
journey_id
touch_time
channel
converted
conversion_value
```

Example:

```csv
journey_id,touch_time,channel,converted,conversion_value
J00001,2025-01-01T10:00:00Z,YouTube,0,0
J00001,2025-01-03T14:00:00Z,Meta,0,0
J00001,2025-01-05T09:00:00Z,Paid Search,1,240
```

`converted=1` and `conversion_value` are placed on the converting touch. Non-converting journeys can also be included; they are useful for path reporting but receive no attribution credit.

## Demo data

The included synthetic dataset contains 1,200 journeys across:

- Meta
- Paid Search
- YouTube
- Email
- Organic
- Direct

The generator intentionally makes some channels more likely to appear early in journeys and others more likely to appear late. That creates a useful demonstration of how first-touch and last-touch rules can tell very different stories.

Rebuild the sample:

```bash
python generate_sample.py
```

## Run the report

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Report views

- Journey/conversion KPI cards
- Selected-model channel credit
- Channel × attribution-model heatmap
- Model-sensitivity ranking
- Side-by-side conversion-credit table
- Most common converting paths
- CSV export

## Project structure

```text
multi-touch-attribution/
├── README.md
├── app.py
├── attribution_models.py
├── generate_sample.py
├── requirements.txt
├── data/
│   └── sample_journeys.csv
└── tests/
    └── test_attribution_models.py
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Measurement note

This is a **rule-based attribution analysis**, not an incrementality or causal model.

All five models redistribute credit across observed touches. None of them prove that a touchpoint caused the conversion. Their value here is to expose how sensitive channel conclusions can be to the attribution rule itself.
