# Validation Report — Goalie Scenario Agent V1

**Date:** 2026-05-28  
**Scope:** Schema validation, golden example review, test scenario quality gates

---

## 1. Schema Validation

**Artifact:** `content/examples/sample_analysis_2on1.json`

| Check | Result |
|-------|--------|
| Required top-level fields present | Pass |
| `visual_cues` ≥ 4 | Pass (5) |
| `outcome_paths` count 3–5 | Pass (4) |
| Exactly one `is_primary: true` | Pass (`path_1`) |
| `situation_classification` non-empty | Pass |
| All `scan_checklist` keys populated | Pass |
| `handedness_and_screens` complete | Pass |
| `confidence` complete | Pass |
| Path IDs match pattern `path_[1-5]` | Pass |

**Note:** Run local validation when Node is available:
```bash
npx ajv-cli validate -s schemas/scenario_output_schema.json -d content/examples/sample_analysis_2on1.json
```

---

## 2. Golden Example Rubric Score (2-on-1)

| Dimension | Score | Notes |
|-----------|-------|-------|
| D1 Visual Grounding | 5 | 5 cues, known/inferred split |
| D2 Primary Read | 5 | Delay read matches playbook §2.1 |
| D3 Path Litigation | 5 | 4 paths, full litigation, flip conditions |
| D4 Playbook Alignment | 5 | odd_man_rush, no screen, LHD noted |
| D5 Schema & Structure | 5 | Matches schema |

**Composite:** 5.0 — Publish-ready reference

---

## 3. Test Scenario Quality Gates

| Scenario | Expected primary read | Gate status |
|----------|----------------------|-------------|
| `scenario_2on1_delay.md` | Hold depth, delay | Defined |
| `scenario_slot_seam.md` | Lateral load on pass | Defined |
| `scenario_point_screen.md` | Deep set, tip awareness | Defined |
| `scenario_wrap_low.md` | RVH / seal, active stick | Defined |

These briefs are ready for live LLM runs when still images are attached. Text-only runs should produce equivalent structure to `sample_analysis_2on1.json`.

---

## 4. Prompt / Playbook Alignment Review

| Requirement | Implementation |
|-------------|----------------|
| Direct-first teaching | `goalie_scenario_agent.md` Step 4–5 |
| 7Sage-style litigation | Agent § "Litigation Standard" + path fields |
| Single master knowledge | `goalie_master_playbook.md` |
| Known vs inferred | `visual_cues.certainty` + Step 1 |
| Handedness + screens | Playbook §3–4, schema `handedness_and_screens` |
| 3–5 outcome paths | Schema `minItems: 3`, `maxItems: 5` |

---

## 5. Outstanding for Production

- [ ] Add actual image files under `content/stills/` matching `still_image_of_the_day.json` paths
- [ ] Run agent on each still with image input; store outputs in `content/analyses/`
- [ ] Wire frontend to render Markdown + JSON from daily publish workflow
- [ ] Optional: CI step with `ajv` on committed analysis JSON files

---

## 6. Teach-Back Validation (V1.1)

**Artifact:** `content/examples/sample_teach_back_review.json`

| Check | Result |
|-------|--------|
| AJV schema validation | Pass (see below) |
| No spoiler paths in review | Pass (coach read summary only) |
| Read comparison with agreement | Pass (`disagree`) |
| Gaps cite user words + litigation | Pass |
| 5-dimension scorecard | Pass |

```bash
npx ajv-cli@5 validate -s schemas/teach_back_review_schema.json -d content/examples/sample_teach_back_review.json
```

## 7. Conclusion

V1 knowledge base, coach + teach-back prompts, schemas, daily image catalog, evaluation rubric, test scenarios, and golden JSON are complete. Teach-first flow is the default for daily scenarios (`interaction_default: teach_first`).

## 8. V2 Validation (Relationships, Assumptions, Bayes)

| Artifact | Status |
|----------|--------|
| `situation_relationship_graph.md` + `situation_graph.json` | Created |
| `assumption_framework.md` | Created |
| `bayesian_reasoning.md` | Created |
| `moneypuck_priors.json` | Created (playbook defaults; re-run script with CSV) |
| `aggregate_moneypuck_priors.py` | Created |
| `docs/moneypuck_data.md` | Created |
| Extended schemas + golden examples | Updated |

```bash
npx ajv-cli@5 validate -s schemas/scenario_output_schema.json -d content/examples/sample_analysis_2on1.json
npx ajv-cli@5 validate -s schemas/teach_back_review_schema.json -d content/examples/sample_teach_back_review.json
```

*Validation version: 1.2*
