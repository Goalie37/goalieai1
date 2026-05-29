# Test Scenario: 2-on-1 Delay

**Simulated still image (describe to agent as if viewing):**

- Rush entering offensive zone, blue line visible.
- Puck carrier (dark jersey) on right wing at top of circle, skating toward net, head up.
- Second attacker (dark jersey) driving middle lane, stick on ice, 10 feet behind carrier.
- One defender (light jersey) backchecking from inside, not yet in passing lane.
- Goalie (you) at top of crease, slightly favoring puck side, on feet, square to carrier.
- No net-front traffic; clear ice to net.
- Carrier's stick: curve visible on left side of blade → **inferred LHD**.
- Backchecker will not arrive before decision at hash marks.

**Metadata (optional):**
```json
{
  "id": "2026-05-26-2on1-delay",
  "situation_hint": "Rush entering zone, backchecker reaching."
}
```

**Quality gates to verify:**
- Primary read: delay / hold depth, do not over-commit to carrier
- Must litigate: challenge early, play pass aggressively, stack on carrier
- Cross-crease pass must appear in scan_checklist and flip_condition on at least one path
- Handedness: LHD inferred from stick
