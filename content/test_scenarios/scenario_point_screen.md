# Test Scenario: Point Shot Layered Screen

**Simulated still image:**

- Puck at center point, shooter in wind-up (college jersey).
- Two teammates in front: one at hash marks, one at crease — layered screen.
- Defender with stick up but not blocking lane.
- Goalie deep in crease, gloves high, sight line partially blocked by front screen.
- Shooter **inferred RHD** from stance at point.
- No weak-side one-timer visible.

**Metadata:**
```json
{
  "id": "2026-05-27-point-shot-layered-screen",
  "situation_hint": "5v5, boxed out net-front."
}
```

**Quality gates:**
- situation_classification includes point_shot_traffic
- screen_types includes layered
- Primary read: stay deep, track puck at release, hands high for tip
- Path litigation for stepping out to see puck early (risk: opening five-hole on low shot)
