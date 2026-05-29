# Goalie Master Playbook

Canonical knowledge base for the Goalie Scenario Agent. All tactical language, heuristics, and response patterns in agent outputs must align with this document.

---

## 1. Core Principles

### 1.1 Depth and Angle

| Cue | Preferred depth | Rationale |
|-----|-----------------|-----------|
| Puck at blue line, no screen | Aggressive (top of crease to above) | Cut angle, challenge shot before traffic arrives |
| Puck below dots with net-front traffic | Conservative (crease to post-crease) | Protect five-hole and short-side on deflections |
| East-west pass threat at slot | Match pass, hold middle | Be set before shot; lateral push beats late scramble |
| Breakaway / partial break | Challenge when puck is committed | Delay until deke or shot is telegraphed |

**Angle rule:** Square to the puck carrier's release point, not the net center. Adjust post when puck moves laterally more than one stick length.

### 1.2 Visual Attachment

1. **Puck** — primary until pass is in flight.
2. **Pass receiver** — snap to new carrier on release; do not chase puck in air.
3. **Stick blade** — for shot vs. pass fake at same wind-up.
4. **Net-front bodies** — peripheral scan between puck touches.

### 1.3 Stance and Timing

- **Set before release:** Feet planted, hands ready, chest slightly forward.
- **RVH / post lean:** When puck is below goal line extended and threat is wrap or short-side jam.
- **Butterfly / hybrid:** When release is imminent from slot or low circle with traffic.
- **Standing / aggressive:** When puck is far, no screen, and you need to cut angle on point shot.

### 1.4 Read Priority Stack (apply in order)

1. Where is the puck and who has it?
2. Is there a one-timer or seam pass available in the next 1–2 seconds?
3. How many layers of screen between you and the puck?
4. Shot handedness vs. your post and glove/blocker presentation?
5. Rebound direction if save is made — who is closest to the crash?

---

## 2. Situation Families

### 2.1 Odd-Man Rush (2-on-1, 3-on-2)

| Element | Read |
|---------|------|
| Puck carrier | Delay depth until pass or shot commitment |
| Trailer / weak-side | Identify late option; don't over-commit to puck |
| Backchecker | Know if you have a blocker on the pass lane |

**Default play:** Hold depth, force puck carrier wide, respect cross-crease pass more than weak-side shot from poor angle.

**Failure mode:** Diving at puck carrier and leaving cross-crease pass open.

### 2.2 Controlled Entry / Rush with Trailer

- Puck on wing with middle drive → track middle drive feet, not just puck.
- Late trailer from blue line → be aware of second touch shot through traffic.

### 2.3 Offensive Zone Cycle (Low)

- Puck on wall below dots → expect walk-out and net-front jam.
- Post integration on strong side; be ready to seal on wrap.
- **Do not** chase puck behind net unless you own the rim and have clear body position.

### 2.4 Low-to-High (Below Goal Line to Point)

- Puck goes from corner to point → you have time to reset depth and find screen layers.
- **Threat:** One-timer through traffic from point; identify shooter's handedness for blocker/glove side.
- Step out only after puck is on point and you're set; don't step while puck is still in motion up the wall.

### 2.5 East-West (Slot / Seam)

- Highest danger: pass across royal road (center ice in front of net).
- **Goalie priority:** Be on top of crease, square to eventual shot, push on pass not on shot.
- Late arrival on seam = scramble; prefer early lateral load.

### 2.6 Net-Front Chaos (Scramble, Rebounds, Screens)

- Freeze when you cover puck and traffic allows whistle or reset.
- Active stick on wrap attempts from below goal line.
- **Rebound control:** Direct to corner or cover; don't punch into slot.

### 2.7 Point Shot with Traffic

- See puck before release; expect redirect, tip, and screen-movement.
- **Depth:** Slightly deeper than clean point shot; hands high for high tips.
- Track stick of net-front player on release.

### 2.8 Breakaway / Penalty Shot

- Match speed, stay patient, read release point.
- Challenge when hands separate or body leans for shot.
- **Deke:** Stay up, take away five-hole last, force wide angle.

---

## 3. Handedness Rules

### 3.1 Terminology

- **LHD shooter:** Shoots left; release from left side of body (from goalie's view: often more dangerous to glove side when attacking from right circle).
- **RHD shooter:** Shoots right; reverse mapping.
- **Off-wing:** Shooter on wing opposite their handedness (e.g., LHD on right wing) — opens one-timer to middle.

### 3.2 Threat Map by Puck Location (General)

| Puck location | LHD typical danger | RHD typical danger |
|---------------|--------------------|--------------------|
| Left circle (goalie's right) | One-timer to far side, wrist far corner | Cut-in, short side if goalie over-commits glove |
| Right circle (goalie's left) | Cut-in, short side | One-timer far side, wrist far corner |
| Slot / middle | Quick release both sides; five-hole on delay | Same |
| Point (center) | Slap through traffic, high glove side bias | Same with blocker side bias on low shots |

### 3.3 Post and Save Selection

- **Strong-side post:** When puck is on same side as shooter and no cross-ice pass threat.
- **RVH / post lean:** Strong-side low threat, wrap, or jam from below goal line.
- **Glove presentation:** High releases from off-wing one-timers; do not drop early.
- **Blocker presentation:** Low slot releases from same-side wing shooters.

### 3.4 Handedness in Agent Responses

Always state: shooter handedness (if visible or inferable), off-wing vs. on-wing, and which post/side is "strong" for this frame.

---

## 4. Screen Taxonomy

| Type | Description | Goalie adjustment |
|------|-------------|-------------------|
| **Single static** | One skater between puck and goalie | Move to see puck around screen side; don't guess through body |
| **Layered** | Two+ bodies, staggered depth | Deepest depth; track puck at last visible moment; expect redirect |
| **Moving / sliding** | Screen shifts at release | Delay reaction until puck exits screen; hands follow puck path |
| **Late screen** | Player moves into lane at release | Most dangerous; stay set, react to puck path not fake wind-up |
| **Stick screen** | Blade in lane only | Smaller visual block; still track puck |

**Rule:** If you cannot see the puck 0.5s before release, default to compact stance and react to first visible puck path — do not pre-guess corner.

---

## 5. Rebound Strategy Matrix

| Situation | Preferred action | Risk if wrong |
|-----------|------------------|---------------|
| Clean save, no crash | Cover or direct to corner | Punch into slot → second chance |
| Save with net-front crash | Control rebound to safe side or freeze | Loose puck in crease |
| High save, puck drops in crease | Quick cover or smother | Swipe that misses → open net |
| Blocker side save, traffic strong side | Rebound to corner or freeze | Rebound to slot |
| Glove side save, weak side open | Control angle of rebound | Wrap or tap-in weak side |

**Freeze criteria:** Puck covered, no immediate stick lift threat, referee can blow play dead or defense can clear.

**Active recovery:** Only when puck is loose, you have line of sight, and no opposing player has inside position on the puck.

---

## 6. Player Scan Checklist

Use on every still image analysis:

1. **Puck carrier** — location, body position, shooting vs. passing intent.
2. **Primary pass option** — open lane, stick on ice, timing.
3. **Net-front** — screens, tips, sticks, handedness.
4. **Weak-side threat** — open player, one-timer lane.
5. **Point / high support** — second wave, low-to-high option.
6. **Defenders** — stick in lane, box-out, backchecker pressure.
7. **Your depth and angle** — are you square, deep enough, set?

---

## 7. Failure Patterns and Corrective Cues

| Failure | Cue that caused it | Correction |
|---------|-------------------|------------|
| Short-side goal | Over-scooted to puck side | Hold post, trust back-side defense |
| Cross-crease goal | Committed to puck carrier early | Delay, stay on feet, respect pass |
| Five-hole on delay | Too aggressive on fake shot | Stay up, read hands |
| Tip / redirect | Lost puck in screen | Track stick, deeper set |
| Wrap | Puck below goal line, flat on post | Seal with RVH, active stick |
| Rebound goal | Punched into slot | Control direction or freeze |
| Late on seam | Reacted to shot not pass | Load lateral on pass release |

---

## 8. Terminology Dictionary

| Term | Definition |
|------|------------|
| **Royal road** | Imaginary line splitting the slot; passes across it create elite chances |
| **Post integration** | Goalie anchored to post on strong-side puck |
| **RVH** | Reverse Vertical Horizontal — post lean with pad on ice |
| **Challenge** | Move out to cut angle on shooter |
| **Delay** | Hold depth, wait for commitment |
| **Seal** | Close five-hole and short side on wrap/low play |
| **Traffic** | Skaters between puck and goalie |
| **Release point** | Where shot leaves stick |
| **Scramble** | Unsettled play after save or loose puck |
| **Set** | Ready stance before shot |
| **Strong side** | Side of net where puck is |
| **Weak side** | Opposite side from puck |
| **Freeze** | Stop play by covering puck |
| **Steer** | Intentionally angle rebound to safe area |

---

## 9. Outcome Path Templates

When generating 3–5 outcome paths, draw from these categories and combine with image-specific cues:

1. **Challenge / aggressive angle** — cut shot angle; risk: pass or deke.
2. **Hold depth / delay** — protect net; risk: shot through traffic unchallenged.
3. **Post lean / RVH** — seal strong side; risk: weak-side play or quick pass out.
4. **Active stick / poke** — disrupt pass or wrap; risk: missing poke, opening five-hole.
5. **Reset / stand up** — prepare for next phase (low-to-high, cycle); risk: not set for immediate shot.
6. **Rebound-first positioning** — play for second chance; risk: first shot beats you clean.

Each path must cite: trigger cue, execution, primary risk, and what would flip the recommendation.

---

## 10. Confidence and Uncertainty

**State explicitly when unknown:**
- Shooter handedness (if jersey number / stick curve not visible)
- Exact puck position (if obscured)
- Score, time, manpower (unless provided in metadata)
- Skater identities beyond visible jerseys

**High confidence when:** puck, carrier, major threats, and your depth/angle are clearly visible.

**Medium confidence when:** screen blocks partial view but primary threat is inferable.

**Low confidence when:** critical information (puck location, carrier, one-timer lane) is not visible — recommend conservative default and list what would change the read.

---

## 11. Response Vocabulary (Agent Must Use)

- Use **primary read** for best play.
- Use **outcome path** for each alternative.
- Use **litigation** for why-right / why-wrong per path.
- Use **scan checklist** for player/threat inventory.
- Use **known** vs. **inferred** for image facts.
- Avoid: "obviously," "always," "never" without cue-based exception.

---

## 12. Teach-Back Protocol (User on Offense)

**Purpose:** The goalie explains the situation *before* receiving the coach breakdown. Teaching forces retrieval practice — you learn what you can articulate, not only what you read.

### 12.1 When to Use

- **Daily still (recommended default):** Image shown → user teaches → agent reviews → optional coach reveal.
- **Review only:** User already submitted teaching; agent scores and corrects.
- **Coach reveal:** Full direct-first analysis after teach-back (user must have taught first unless admin bypass).

### 12.2 What the User Must Teach (Minimum)

| Block | User explains |
|-------|----------------|
| **Situation** | What play family is this? (rush, seam, point shot, etc.) |
| **Visual cues** | At least 4 facts they see (puck, threats, screens, their depth) |
| **Scan** | Carrier, pass option, net-front, weak side, point, defenders, self |
| **Primary read** | What they would do and why |
| **Biggest threat** | What beats them if they're wrong |
| **One alternative** | Another play they considered and why they rejected or weighed it |
| **Uncertainty** | What they are not sure about from the image |

### 12.3 Agent Review Rules (Teach-Back Mode)

1. **Do not** dump the full direct-first analysis until the user has submitted teaching OR explicitly asks for coach reveal after review.
2. **Lead with credit:** Name what the user got right, tied to specific cues they cited.
3. **Litigate gaps:** Missing threats, wrong situation label, weak scan, read that contradicts image — 7Sage style ("You said X; that works when Y, but here Z").
4. **Compare reads:** User primary read vs. coach primary read — agree, partial agree, or disagree with reasons.
5. **Assign gaps:** List 1–3 study points from playbook sections to re-read.
6. **Score teaching** (1–5 per dimension): visual grounding, scan completeness, read quality, threat identification, honesty on uncertainty.

### 12.4 Teach-Back Scoring Dimensions

| Dimension | 5 = exemplary | 1 = fail |
|-----------|---------------|----------|
| **Visual grounding** | ≥ 4 accurate cues, known vs. unsure labeled | Generic or wrong cues |
| **Scan completeness** | All 7 scan areas addressed | Missed major threat (e.g., seam, cross-crease) |
| **Read quality** | Play matches cues and playbook | Read contradicts image or situation |
| **Threat ID** | Names what beats them specifically | Vague ("they might score") |
| **Metacognition** | States real uncertainties | False certainty or no uncertainty |

### 12.5 After Review — Coach Reveal

When user requests coach breakdown (or `coach_reveal` phase):

- Deliver standard direct-first analysis per Section 11.
- Add **teach-back delta:** bullet list of what changed vs. their teaching and why.
- Do not shame; frame deltas as "coach add" not "you failed."

---

## 13. Situation Relationships

Goaltending reads are a **network**, not isolated rules. See [situation_relationship_graph.md](situation_relationship_graph.md) and [situation_graph.json](situation_graph.json).

- **often_follows** — play trends (cycle → low-to-high)
- **enables** — cue makes threat live (open seam → one-timer)
- **supports_read** / **contradicts_read** — when a read fits or fails
- **branches_to** — option tree (delay → shot | pass | deke)

Coach reveal must include a **Relationship Map** (3–5 edges). Teach-back must include at least one relationship from the user.

---

## 14. Assumptions (Must / Could / Doesn't Need)

See [assumption_framework.md](assumption_framework.md).

| Tier | Use |
|------|-----|
| **Must happen** | Necessary for main threat to beat you |
| **Could happen** | Live branches (maps to Bayesian branches) |
| **Doesn't need to happen** | Ruled out here — justify with cues |

False **must** assumptions are the top teach-back litigation target.

---

## 15. Bayesian Priors (MoneyPuck)

See [bayesian_reasoning.md](bayesian_reasoning.md) and [moneypuck_priors.json](moneypuck_priors.json).

- Priors from MoneyPuck shot aggregates ([data.htm](https://moneypuck.com/data.htm)) — **credit MoneyPuck.com**
- Still image supplies likelihood updates; output posterior **bands**, not fake exact xG
- Refresh: `python3 scripts/aggregate_moneypuck_priors.py`

---

*Version: 1.2 — GoalieAI Scenario Agent*
