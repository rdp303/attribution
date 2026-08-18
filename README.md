# Meta Attribution Window Explorer

An interactive report for understanding how **Meta Ads campaign performance changes under different attribution windows**.

Instead of accepting one Ads Manager attribution setting at face value, the app re-queries the same campaign performance across a click/view attribution matrix and compares reported conversions, CPA, conversion value, and ROAS.

## What it answers

- How much does reported ROAS change between 1-day and 7-day click attribution?
- How much additional credit appears when a view-through window is included?
- Which campaigns are most sensitive to attribution-window choice?
- Does a campaign still look efficient under a more conservative window?
- How different are reported conversions, CPA, and revenue from the team's baseline setting?

## Report views

- KPI cards for a selected attribution setting vs. baseline
- Attribution-sensitivity chart across every standard scenario
- Click × view heatmap for ROAS, CPA, or conversions
- Campaign-level table with deltas vs. baseline
- Full scenario comparison table
- CSV export of normalized results
- Demo mode that works without Meta credentials

## Attribution scenarios

The report focuses on the standard click/view windows exposed by Meta's Ads Insights API:

```text
Click: 1d_click, 7d_click, 28d_click
View:  1d_view, 7d_view, 28d_view
```

It evaluates 15 scenarios:

- 3 click-only windows
- 3 view-only windows
- all 9 click × view combinations

The current Meta Business SDK also exposes specialized attribution modes such as DDA, incrementality, SKAN, and engaged-view options. Those are intentionally not mixed into the default matrix because they represent different measurement frameworks rather than directly comparable click/view windows.

## Why each combination is queried separately

The tool sends the exact requested `action_attribution_windows` for each scenario and uses the scenario-level `value` returned in Meta's `actions` / `action_values` arrays.

It **does not sum separate click and view fields** to manufacture a combined result. The same conversion can qualify for more than one window, so naïvely adding window-specific counts can overstate conversions.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens in **Demo data** mode automatically.

## Live Meta API mode

Create a Meta app with Marketing API access and use an access token that can read the target ad account.

You can enter credentials in the Streamlit sidebar or set:

```bash
export META_ACCESS_TOKEN='...'
export META_AD_ACCOUNT_ID='1234567890'
export META_API_VERSION='v25.0'
streamlit run app.py
```

The Graph API version is configurable because Meta versions the Marketing API over time.

### API request pattern

For every attribution scenario the app requests Ads Insights with fields including:

```text
campaign_id
campaign_name
spend
impressions
clicks
actions
action_values
```

and parameters including:

```text
level=campaign
action_attribution_windows=[...]
action_report_time=conversion
use_unified_attribution_setting=false
```

`use_unified_attribution_setting=false` is intentional: the purpose of the report is to compare custom attribution scenarios rather than force the ad set's configured attribution setting.

## Conversion action

The default conversion action is:

```text
purchase
```

For a real account, enter the action type returned by your Meta Insights data. The report calculates:

```text
CPA  = spend / attributed conversions
ROAS = attributed conversion value / spend
```

Spend, impressions, and clicks should remain constant across attribution scenarios. The attributed conversion metrics are what change.

## Project structure

```text
.
├── app.py                 # Streamlit report
├── attribution.py         # scenario + metric logic
├── meta_api.py            # Meta Ads Insights client
├── generate_sample.py     # reproducible demo dataset generator
├── data/
│   └── sample_attribution.csv
├── tests/
│   └── test_attribution.py
├── requirements.txt
└── .github/workflows/test.yml
```

## Rebuild demo data

```bash
python generate_sample.py
```

The sample dataset is synthetic and exists only to make the report immediately usable without credentials.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Measurement note

This project is an **attribution sensitivity analysis**, not an incrementality model. A longer attribution window will usually give Meta more opportunities to claim conversion credit. That does not prove those additional conversions were caused by the ads.

The report is useful precisely because it makes that sensitivity visible instead of hiding it behind one default attribution setting.
