# Bayesian Reasoning Guide

How the agent combines **MoneyPuck league priors** with **still-image evidence** to explain branches — without claiming pixel-exact xG for a frozen frame.

Data source: [moneypuck_priors.json](moneypuck_priors.json) (aggregated from [moneypuck.com/data.htm](https://moneypuck.com/data.htm)). **Credit MoneyPuck.com** in every coach reveal that cites priors.

---

## Model (Conceptual)

```
posterior(branch) ∝ prior(branch | situation_bucket) × likelihood(branch | visual_cues)
```

- **Prior:** From `moneypuck_priors.json` for the matched playbook bucket (e.g., `odd_man_rush`, `5v5`).
- **Likelihood:** Qualitative shifts from cues visible in the still (open seam, late backchecker, screen type).
- **Posterior:** Reported as bands: `high` (>~40% relative weight), `medium` (~15–40%), `low` (<~15%). Optional % ranges with disclaimer.

---

## Protocol (Coach Reveal)

1. **Classify frame** → `situation_classification` + MoneyPuck bucket key.
2. **Lookup prior** in `moneypuck_priors.json` → `branches[]` with `p_goal`, `p_rebound`, etc.
3. **List cue-based likelihood shifts** — "open middle drive" → upweight `pass_branch`.
4. **Emit `bayesian_branches`** — one row per live branch with `prior_band`, `posterior_band`, `evidence_for`, `evidence_against`.
5. **Sensitivity** — one "if X were different" line per major branch.
6. **Attribution** — include `prior_source: moneypuck` and season range from JSON metadata.

---

## Language Rules

| Do | Don't |
|----|-------|
| "League prior for rush shots at 5v5…" | "This shot has 0.34 xG" (unless citing prior aggregate) |
| "Posterior shifts to pass branch because…" | "They will definitely pass" |
| Label `playbook_default` when no MP bucket match | Invent percentages without prior row |

---

## Mapping Still → MoneyPuck Bucket

| Playbook family | Bucket key in priors JSON |
|-----------------|---------------------------|
| odd_man_rush | `odd_man_rush_5v5` (proxy from medium-danger if only goalie season data) |
| east_west_seam | `slot_seam_5v5` |
| point_shot_traffic | `point_shot_traffic_5v5` |
| net_front_chaos | `net_front_rebound_5v5` |
| low_to_high | `league_5v5` or `point_shot_traffic_5v5` |
| breakaway | `medium_danger_5v5` |
| oz_cycle_low | `slot_seam_5v5` (high danger proxy) |

**Data types:** `moneypuck_priors.json` includes `data_type`: `goalie_season_summary` (your current file) or `shot_level` when shot CSVs are added.

Split by `manpower` when still metadata or visible special teams context: `5v5`, `5v4`, `4v5`.

---

## Integration with Assumptions

| Assumption tier | Bayesian role |
|-----------------|-----------------|
| Must happen | Conditions for a branch's likelihood to matter |
| Could happen | Branch set for prior/posterior |
| Doesn't need | Branches with near-zero posterior after cues |

Litigate false **must** = you overweighted a branch inconsistent with posterior.

---

## Refresh

Re-run `scripts/aggregate_moneypuck_priors.py` when new season CSVs are downloaded. Update `generated_at` in priors JSON.

---

*Guide version: 1.0*
