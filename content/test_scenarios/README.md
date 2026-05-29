# Test Scenarios

Text-based scenario briefs simulate still images for prompt validation when image files are not yet in `content/stills/`. Use with `prompts/goalie_scenario_agent.md` + `knowledge/goalie_master_playbook.md`.

## How to Run a Validation Pass

1. Open Cursor Agent (or your LLM) with `goalie_scenario_agent.md` as system/context.
2. Attach `goalie_master_playbook.md`.
3. Paste one scenario brief from this folder.
4. Score output with `docs/evaluation_rubric.md`.
5. Validate JSON against `schemas/scenario_output_schema.json`.

## Scenarios

| File | Playbook family | Primary read expectation |
|------|-----------------|------------------------|
| `scenario_2on1_delay.md` | odd_man_rush | Hold depth, delay, respect cross-crease |
| `scenario_slot_seam.md` | east_west_seam | Lateral load on pass, set before shot |
| `scenario_point_screen.md` | point_shot_traffic | Deeper set, track stick, expect tip |
| `scenario_wrap_low.md` | oz_cycle_low | Post integration / RVH, active stick |

Golden reference JSON: `../examples/sample_analysis_2on1.json`

## Teach-back testing

| File | Purpose |
|------|---------|
| `teach_back_sample_submission.md` | Simulated user teaching (weak 2-on-1 read) |
| `../examples/sample_teach_back_review.json` | Expected agent review output |

Flow: `goalie_teach_back_mode.md` + submission → validate against `teach_back_review_schema.json`
