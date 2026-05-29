# GoalieAI — Scenario Agent

7Sage-style goaltending coach for still images. **Teach-first** flow, then coach reveal with:

- **Relationships** — how situations, cues, threats, and reads connect
- **Assumptions** — must happen / could happen / doesn't need to happen
- **Bayesian branches** — MoneyPuck league priors + image-based updates (credit [MoneyPuck.com](https://moneypuck.com/data.htm))

## Quick Start

| Resource | Path |
|----------|------|
| Playbook | [`knowledge/goalie_master_playbook.md`](knowledge/goalie_master_playbook.md) |
| Relationship graph | [`knowledge/situation_relationship_graph.md`](knowledge/situation_relationship_graph.md) |
| Assumptions | [`knowledge/assumption_framework.md`](knowledge/assumption_framework.md) |
| Bayesian guide | [`knowledge/bayesian_reasoning.md`](knowledge/bayesian_reasoning.md) |
| MoneyPuck priors | [`knowledge/moneypuck_priors.json`](knowledge/moneypuck_priors.json) |
| Teach-back prompt | [`prompts/goalie_teach_back_mode.md`](prompts/goalie_teach_back_mode.md) |
| Coach prompt | [`prompts/goalie_scenario_agent.md`](prompts/goalie_scenario_agent.md) |
| User worksheet | [`content/teach_back_template.md`](content/teach_back_template.md) |

### Daily flow

1. Load `goalie_teach_back_mode.md` + playbook + relationship/assumption docs
2. Show still only → user completes teach-back (includes assumptions + one relationship)
3. Agent reviews → [`teach_back_review_schema.json`](schemas/teach_back_review_schema.json)
4. User says **coach reveal** → `goalie_scenario_agent.md` + `moneypuck_priors.json`
5. Output includes assumptions, relationship map, Bayesian branches, outcome paths

### MoneyPuck priors

See [`docs/moneypuck_data.md`](docs/moneypuck_data.md).

```bash
# After downloading shot CSV to data/moneypuck/raw/
python3 scripts/aggregate_moneypuck_priors.py --input data/moneypuck/raw/
```

## Local App

Single-still teach-back UI that talks to the Claude API.

Uses the Claude Agent SDK — reuses your local Claude Code login, no separate API key.

```bash
pip install -r app/requirements.txt
# make sure `claude` CLI is installed and you're logged in:
#   npm install -g @anthropic-ai/claude-code && claude login
python app/server.py
# open http://127.0.0.1:8000
```

Scenarios live as JSON in `viewer/scenes/` — the teach-back UI embeds the **interactive 3D viewer** (orbit, camera presets). Coach review uses the scene data (positions, roles, situation family), not flat images. Optional PNG exports in `content/stills/` are only for sharing; the app does not require them.

Author or edit scenes at **http://127.0.0.1:8000/viewer/** (see [`viewer/README.md`](viewer/README.md)). Supplemental tags/levels merge from `content/still_image_of_the_day.json` by matching each scene's `id`.

## Repository Layout

```
goalieai/
├── knowledge/
│   ├── goalie_master_playbook.md
│   ├── situation_relationship_graph.md
│   ├── situation_graph.json
│   ├── assumption_framework.md
│   ├── bayesian_reasoning.md
│   └── moneypuck_priors.json
├── prompts/
│   ├── goalie_teach_back_mode.md
│   └── goalie_scenario_agent.md
├── schemas/
├── scripts/
│   └── aggregate_moneypuck_priors.py
├── data/moneypuck/raw/          # gitignored CSVs
├── content/
└── docs/moneypuck_data.md
```

## Quality Gates (V2)

- Assumptions: must / could / doesn't need
- Relationship map: 3–5 edges
- Bayesian branches: prior + posterior + MoneyPuck attribution
- Teach-back litigates false **must** assumptions
- One primary read + 3–5 outcome paths

See [`docs/evaluation_rubric.md`](docs/evaluation_rubric.md).
