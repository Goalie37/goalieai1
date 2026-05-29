# Test Scenario: Wrap Below Goal Line

**Simulated still image:**

- Puck below goal line on goalie's glove side (left side of rink), carrier behind net.
- Carrier body low, stick on puck, path toward far post wrap.
- No immediate pass option visible; one defender on post side.
- Goalie on post, pad down on strong side, stick toward puck — RVH posture.
- Youth level pace; no extra traffic in crease.

**Metadata:**
```json
{
  "id": "2026-05-25-wrap-below-goal-line",
  "situation_hint": "Cycle, puck below goal line strong side."
}
```

**Quality gates:**
- oz_cycle_low in classification
- Primary read: seal / RVH, active stick, do not chase behind net
- Must litigate: poke check behind net, stand up and reset (wrong for immediate wrap)
- confidence may be high — clear puck location and threat
