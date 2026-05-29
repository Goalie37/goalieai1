# Goalie Scenario Agent — Evaluation Rubric

Use this rubric to score agent outputs (human review or automated checks). Target: **≥ 4.0 / 5.0** average on all dimensions before publishing a daily scenario.

**Scale:** 1 = fails requirement | 3 = acceptable | 5 = exemplary

---

## Dimension 1: Visual Grounding (Weight: 25%)

| Score | Criteria |
|-------|----------|
| 5 | ≥ 6 cues, all tied to paths; known/inferred labeled correctly; no invented facts |
| 4 | ≥ 4 cues, labeled; minor inference overstated but recoverable |
| 3 | ≥ 4 cues but weak linkage to recommendations |
| 2 | < 4 cues or generic cues ("traffic in front") |
| 1 | Hallucinated players, puck location, or game state |

**Fail gate:** Any hallucinated fact → cap dimension at 2.

---

## Dimension 2: Primary Read Quality (Weight: 25%)

| Score | Criteria |
|-------|----------|
| 5 | Clear play + why_now cites 2+ cues + primary_risk is situation-specific |
| 4 | Clear play; why_now adequate; risk generic but valid |
| 3 | Play reasonable but why_now thin or partly generic |
| 2 | Play contradicts visible cues or playbook |
| 1 | No primary read or contradicts another section |

**Cross-check:** Primary read must match exactly one `is_primary: true` path in JSON.

---

## Dimension 3: Outcome Path Litigation (Weight: 25%)

| Score | Criteria |
|-------|----------|
| 5 | 3–5 paths; each has complete why_right / why_wrong / flip_condition; 7Sage-style tradeoffs |
| 4 | All paths complete; litigation present but one path shallow |
| 3 | 3–5 paths; one field missing or repetitive across paths |
| 2 | < 3 paths or litigation missing on multiple paths |
| 1 | Paths are generic templates not tied to image |

**Fail gate:** Not exactly one primary path → cap dimension at 2.

---

## Dimension 4: Playbook Alignment (Weight: 15%)

| Score | Criteria |
|-------|----------|
| 5 | Correct situation family, handedness, screen type, terminology from master playbook |
| 4 | Minor terminology drift; tactics correct |
| 3 | One misclassification (e.g., rush labeled as cycle) but reads still defensible |
| 2 | Multiple misclassifications or non-playbook advice |
| 1 | Ignores playbook structure |

---

## Dimension 6: Assumptions & Relationships (Weight: 15%) — V2 coach output

| Score | Criteria |
|-------|----------|
| 5 | Full must/could/doesn't need; 3–5 relationship edges; tied to cues |
| 4 | Assumptions present; relationships mostly valid |
| 3 | Thin assumptions or generic relationships |
| 2 | Missing assumptions or no relationship map |
| 1 | Contradictory must claims |

## Dimension 7: Bayesian Calibration (Weight: 10%) — V2 coach output

| Score | Criteria |
|-------|----------|
| 5 | Prior from moneypuck_priors; posterior shifts cite cues; attribution present |
| 4 | Bands present; minor prior mismatch |
| 3 | Bands present but weak evidence linkage |
| 2 | Fake exact xG or no attribution |
| 1 | No bayesian_branches |

**Recalculate composite for V2 coach analysis:** D1–D5 (original weights scaled to 75%) + D6 (15%) + D7 (10%).

---

## Dimension 5: Schema & Structure (Weight: 10%)

| Score | Criteria |
|-------|----------|
| 5 | Valid JSON per schema; Markdown mirrors JSON; scan_checklist complete |
| 4 | Valid JSON; small optional field omission |
| 3 | JSON valid with extra properties or minor type issues |
| 2 | JSON missing required sections |
| 1 | No JSON or invalid structure |

---

## Composite Score

```
total = (D1 × 0.25) + (D2 × 0.25) + (D3 × 0.25) + (D4 × 0.15) + (D5 × 0.10)
```

| Total | Action |
|-------|--------|
| ≥ 4.0 | Publish-ready |
| 3.0 – 3.9 | Revise prompt/playbook or re-run analysis |
| < 3.0 | Do not publish; root-cause review |

---

## Automated Checklist (Pre-Human Review)

- [ ] `outcome_paths.length` between 3 and 5
- [ ] Exactly one path with `is_primary: true`
- [ ] `visual_cues.length` ≥ 4
- [ ] Each cue has `certainty` in `known` | `inferred`
- [ ] `confidence.unknowns` non-empty when `confidence.level` is `low`
- [ ] `situation_classification` non-empty
- [ ] All scan_checklist keys populated (non-empty strings)
- [ ] JSON validates against `schemas/scenario_output_schema.json`

---

## Reviewer Worksheet

```
Scenario ID: _______________
Reviewer: _______________
Date: _______________

D1 Visual Grounding:     __ / 5
D2 Primary Read:         __ / 5
D3 Path Litigation:      __ / 5
D4 Playbook Alignment:   __ / 5
D5 Schema & Structure:   __ / 5

Composite: __ / 5

Notes:
-
-

Publish?  [ ] Yes  [ ] Revise  [ ] Reject
```

---

---

## Teach-Back Review Rubric (Separate from Coach Analysis)

Use when scoring agent output from **review_teaching** mode (`teach_back_review_schema.json`). Target composite **≥ 3.5** before publishing teach-back flow.

| Dimension | Weight | 5 = exemplary | 1 = fail |
|-----------|--------|---------------|----------|
| **Credits accuracy** | 20% | Every "got right" tied to user's words + image | False praise |
| **Gap litigation** | 30% | Each gap quotes user + 7Sage litigation + playbook ref | Generic correction |
| **Read comparison** | 20% | agreement + why + both summaries accurate | Missing or vague |
| **Actionable next step** | 15% | Clear retry vs. coach reveal | No next step |
| **Schema & scores** | 15% | All 5 dimension scores + composite; valid JSON | Missing scores |

**Fail gates:**
- Reveals full primary read + paths during review-only → cap at 2.0
- No gaps when user missed major threat → cap Gaps at 2

**Sample golden:** `content/examples/sample_teach_back_review.json`

---

*Rubric version: 1.1*
