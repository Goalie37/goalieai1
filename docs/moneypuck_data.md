# MoneyPuck Data — GoalieAI

Official source: [moneypuck.com/data.htm](https://moneypuck.com/data.htm)

## License and attribution

- Data is free for **non-commercial** use and journalist ad-hoc use per MoneyPuck terms.
- **Credit MoneyPuck.com** wherever aggregated priors inform coach output.
- Do **not** scrape the MoneyPuck website beyond official download links on the data page.
- Commercial use → contact MoneyPuck at [email protected].

Coach reveal footer (when citing priors):

> Branch rates are league priors from MoneyPuck.com shot data ([seasons listed in moneypuck_priors.json]). This still is explained with image-specific updates, not a claim of exact play-by-play match.

## What we download

| Dataset | Use in GoalieAI |
|---------|-----------------|
| **Shot data** (ZIP → CSV) | Primary — `scripts/aggregate_moneypuck_priors.py` |
| **Data dictionary** | Column mapping — save to `data/moneypuck/dictionary/` |
| Player biography | Optional — handedness validation |
| Season / game goalies | Optional — future context |

**Recommended for development:** Recent Seasons (2018–2024) or a single season ZIP (~120k shots) for faster iteration.

## Local layout

```
data/moneypuck/
  goalies_2008_to_2024.csv   # Season goalie summary (supported now)
  raw/                       # Shot-level CSV extracts (optional, gitignored)
  dictionary/                # Data dictionary
knowledge/
  moneypuck_priors.json      # Generated — committed
```

## Setup

**Option A — Goalie season summary (what you have now)**

1. Place `goalies_*.csv` from [data.htm](https://moneypuck.com/data.htm) in `data/moneypuck/`.
2. Run:

```bash
python3 scripts/aggregate_moneypuck_priors.py --input data/moneypuck/
```

Produces league rates by manpower (5v5, PP, PK) and danger tier (high ≈ slot/seam, low ≈ point). Rush buckets use proxies until shot data is added.

**Option B — Shot-level (best for situation buckets)**

1. Download shot ZIP from data.htm.
2. Extract to `data/moneypuck/raw/`.
3. Run the same command (script auto-detects shot vs goalie CSV).

5. Commit updated `knowledge/moneypuck_priors.json`.

## Refresh cadence

2025–26 shot data is updated nightly on MoneyPuck. Re-aggregate when you want current-season priors.
