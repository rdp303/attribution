# Data Dictionary

| Column | Type | Role | Description |
|---|---|---|---|
| `DATE` | date | time index | Week start date in `YYYY-MM-DD` format |
| `signups` | integer | dependent variable | Weekly signup volume |
| `facebook_impressions` | numeric | paid media exposure | Weekly Facebook/Meta impressions |
| `ppc_impressions` | numeric | paid media exposure | Weekly paid-search/PPC impressions |
| `youtube_impressions` | numeric | paid media exposure | Weekly YouTube impressions |
| `facebook_spend` | numeric | paid media spend | Weekly Facebook/Meta spend |
| `ppc_spend` | numeric | paid media spend | Weekly paid-search/PPC spend |
| `youtube_spend` | numeric | paid media spend | Weekly YouTube spend |

## Modeling mapping

```text
dep_var:
  signups

paid_media_vars:
  facebook_impressions
  ppc_impressions
  youtube_impressions

paid_media_spends:
  facebook_spend
  ppc_spend
  youtube_spend
```

The order of `paid_media_vars` and `paid_media_spends` is intentionally aligned channel-by-channel.
