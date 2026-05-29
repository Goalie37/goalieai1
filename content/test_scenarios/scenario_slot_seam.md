# Test Scenario: Slot Seam Pass

**Simulated still image:**

- Puck on right half-wall, below dot, carrier facing middle.
- Open teammate at slot (royal road) with stick on ice, one-timer ready — **inferred RHD** on weak side.
- Two defenders: one between carrier and net, one late to seam.
- Goalie at top of crease, slightly deep, hips not fully loaded to weak side.
- Net-front: one dark jersey screening, static, between goalie and puck carrier.
- Screen type: single static from net-front; seam pass is primary danger.

**Metadata:**
```json
{
  "id": "2026-05-28-slot-seam-pass",
  "situation_hint": "PP, low-to-high then across slot."
}
```

**Quality gates:**
- Primary read: lateral push / load on pass, be set before one-timer
- Must NOT recommend challenging carrier while seam is open
- east_west_seam in situation_classification
- flip_condition: if seam covered, challenge becomes viable
