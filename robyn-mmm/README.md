# Three-Channel MMM with Meta Robyn

A compact Marketing Mix Modeling project using Meta's open-source **Robyn** package to estimate how Facebook, PPC, and YouTube contribute to weekly signups.

The project uses **impressions as the modeled media exposure variables** and keeps **spend as a paired input** so Robyn can estimate efficiency and support downstream budget-allocation analysis.

## Business question

> How many weekly signups are associated with Facebook, PPC, and YouTube after accounting for carryover, diminishing returns, trend, seasonality, and holidays?

This project is intentionally small enough to understand end-to-end while still using Robyn's core MMM workflow.

## Data

The included synthetic dataset contains **156 weekly observations (3 years)**.

```text
DATE
signups
facebook_impressions
ppc_impressions
youtube_impressions
facebook_spend
ppc_spend
youtube_spend
```

`signups` is the dependent variable. The three impression columns are the `paid_media_vars`; the corresponding spend columns are the `paid_media_spends`.

See [`data_dictionary.md`](data_dictionary.md) for the schema.

## Model specification

The starter model uses:

- Dependent variable: `signups`
- Dependent variable type: `conversion`
- Paid channels: Facebook, PPC, YouTube
- Exposure metrics: impressions
- Spend metrics: weekly channel spend
- Time-series controls: Prophet trend, seasonality, and US holidays
- Adstock: geometric
- Saturation: Robyn Hill-function transformations
- Regression: ridge
- Hyperparameter optimization: Nevergrad
- Model comparison: Pareto-front outputs

The geometric adstock ranges are deliberately broad starter assumptions. They should be tightened with business knowledge or calibration evidence in a real model.

## Install

Robyn's R implementation is the primary version used here.

In R:

```r
install.packages("Robyn")
```

Robyn also requires a one-time Nevergrad setup through Python/`reticulate`. Follow the current Robyn installation guide for that environment setup before running the model.

## Run

From this folder:

```bash
Rscript run_robyn.R
```

By default the script uses the same optimization scale as Meta's current demo:

```text
iterations = 2000
trials = 5
```

For a faster smoke test:

```bash
ROBYN_ITERATIONS=500 ROBYN_TRIALS=2 Rscript run_robyn.R
```

Generated Robyn artifacts are written to:

```text
outputs/
```

Robyn can generate model one-pagers, Pareto model tables, media transformation matrices, decompositions, and other diagnostic output.

## Use your own data

Replace:

```text
data/sample_mmm.csv
```

with a weekly file following the same schema, or update the column names in `run_robyn.R`.

For a real production model, also consider adding important non-media drivers such as:

- promotions
- pricing
- holidays/events not captured automatically
- product launches
- organic traffic/activity
- macroeconomic variables
- competitor activity

Leaving major demand drivers out can cause the media variables to absorb effects that belong elsewhere.

## Why impressions instead of only spend?

Media exposure is usually closer to the actual advertising pressure consumers received. Spend is still retained because Robyn uses spend alongside exposure for media-efficiency and allocation outputs.

That makes the model structure:

```text
Weekly signups
    ~ Facebook impressions
    + PPC impressions
    + YouTube impressions
    + trend
    + seasonality
    + holidays
```

with adstock, saturation, and regularized regression applied inside Robyn.

## Sample data

The sample data is synthetic and exists only to make the project reproducible. It contains:

- different weekly patterns for each channel
- channel-specific spend/impression relationships
- simulated carryover
- diminishing media returns
- underlying trend and seasonality
- random noise

Rebuild it with:

```bash
python generate_sample.py
```

## Interpretation

Robyn returns a set of Pareto-optimal candidate models rather than a single magically "correct" model. Model selection should consider statistical fit, decomposition realism, response curves, business knowledge, and — where available — experiment/lift calibration.

This is a portfolio/demo MMM, not a causal claim about real advertising performance.
