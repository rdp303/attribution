# Marketing Attribution & Measurement Projects

A collection of practical marketing measurement projects focused on attribution, media effectiveness, and incrementality.

## Projects

### 1. Meta Attribution Window Explorer

**Folder:** [`meta-attribution-windows/`](meta-attribution-windows/)

Interactive Python/Streamlit report that compares Meta Ads campaign performance across click/view attribution-window combinations and shows how reported conversions, CPA, revenue, and ROAS change as the attribution rule changes.

### 2. Robyn Marketing Mix Model

**Folder:** [`robyn-mmm/`](robyn-mmm/)

A three-channel Marketing Mix Model built with Meta's open-source **Robyn** package. It models weekly **signups** using Facebook, PPC, and YouTube impressions, while retaining channel spend for ROI and budget-allocation outputs.

The sample project demonstrates:

- weekly MMM data preparation
- exposure-based media inputs
- spend + exposure pairing
- Prophet trend/seasonality/holiday controls
- geometric adstock
- saturation curves
- ridge regression
- Nevergrad hyperparameter optimization
- Pareto model comparison

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
└── .github/workflows/
```

Each project is intentionally self-contained so it can be run, reviewed, or extended independently.
