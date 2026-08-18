# Marketing Attribution & Measurement Projects

A collection of practical marketing measurement projects focused on attribution, media effectiveness, and incrementality.

## Projects

### 1. Meta Attribution Window Explorer

**Folder:** [`meta-attribution-windows/`](meta-attribution-windows/)

Interactive Python/Streamlit report that compares Meta Ads campaign performance across click/view attribution-window combinations and shows how reported conversions, CPA, revenue, and ROAS change as the attribution rule changes.

### 2. Robyn Marketing Mix Model

**Folder:** [`robyn-mmm/`](robyn-mmm/)

A three-channel Marketing Mix Model built with Meta's open-source **Robyn** package. It models weekly **signups** using Facebook, PPC, and YouTube impressions, while retaining channel spend for ROI and budget-allocation outputs.

The sample project demonstrates weekly MMM data preparation, exposure-based media inputs, spend + exposure pairing, Prophet controls, geometric adstock, saturation, ridge regression, Nevergrad optimization, and Pareto model comparison.

### 3. CPC Click Response / Decay Model

**Folder:** [`cpc-click-decay-model/`](cpc-click-decay-model/)

A grouped spend-response model for paid search or other CPC media. It fits a power curve between spend and clicks for each campaign group and translates the fitted curve into click elasticity, average CPC, marginal CPC, and marginal clicks per additional $1,000 of spend.

The grouping variable is configurable, so the same analysis can compare campaign type, brand vs. non-brand, market, product line, audience, keyword theme, or device.

### 4. Multi-Touch Attribution Playground

**Folder:** [`multi-touch-attribution/`](multi-touch-attribution/)

Interactive journey-level attribution analysis comparing first-touch, last-touch, linear, time-decay, and 40/20/40 position-based attribution on the same customer paths.

The project highlights how channel credit can move substantially even when the underlying customer journeys do not change. It includes a configurable time-decay half-life, channel-by-model sensitivity analysis, common converting paths, and synthetic demo journeys across Meta, Paid Search, YouTube, Email, Organic, and Direct.

## Repository structure

```text
attribution/
├── meta-attribution-windows/
│   ├── README.md
│   ├── app.py
│   ├── attribution.py
│   ├── meta_api.py
│   ├── generate_sample.py
│   ├── requirements.txt
│   ├── data/
│   └── tests/
│
├── robyn-mmm/
│   ├── README.md
│   ├── run_robyn.R
│   ├── generate_sample.py
│   ├── data_dictionary.md
│   ├── data/
│   └── outputs/
│
├── cpc-click-decay-model/
│   ├── README.md
│   ├── app.py
│   ├── click_decay.py
│   ├── generate_sample.py
│   ├── requirements.txt
│   ├── data/
│   └── tests/
│
├── multi-touch-attribution/
│   ├── README.md
│   ├── app.py
│   ├── attribution_models.py
│   ├── generate_sample.py
│   ├── requirements.txt
│   └── tests/
│
└── .github/workflows/
```

Each project is intentionally self-contained so it can be run, reviewed, or extended independently.
