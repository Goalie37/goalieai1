"""Turn a single MoneyPuck shot row into a viewer scene + analysis context.

The shot row gives us the shooter's coordinate plus the actual F/D counts on
each team (shootingTeamForwardsOnIce, defendingTeamDefencemenOnIce, etc.). We
place every skater on the ice: shooter + (off_F + off_D − 1) supporting
offensive skaters + (def_F + def_D) defenders + goalie. Positions are
heuristic anchors keyed to family and puck location — not real tracking — but
the *count* matches the shot's actual on-ice state.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from shot_to_scene import classify_family, default_camera, facing_toward_net, goalie_on_angle  # type: ignore  # noqa: E402


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _as_int(v: Any, default: int = 0) -> int:
    f = _as_float(v, float(default))
    try:
        return int(f)
    except (TypeError, ValueError):
        return default


def _as_str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    try:
        if isinstance(v, float) and math.isnan(v):
            return default
    except TypeError:
        pass
    return str(v)


def _sk(eid: str, label: str, team: str, role: str, x: float, y: float, stick: str) -> dict:
    return {
        "id": eid,
        "label": label,
        "team": team,
        "role": role,
        "x": round(float(x), 1),
        "y": round(float(y), 1),
        "facing": facing_toward_net(x, y),
        "stick": stick,
    }


def _clamp_y(y: float, margin: float = 2.0) -> float:
    return max(-42.5 + margin, min(42.5 - margin, y))


def _clamp_x(x: float, lo: float = 5.0, hi: float = 99.0) -> float:
    return max(lo, min(hi, x))


# Anchor templates per (family, side). `side` = sign(puck_y) (1 strong side toward +y, −1 toward −y).
# Each entry is a list of (label, role, x, y_factor) — y_factor multiplies by `side`.
OFFENSE_ANCHORS = {
    "odd_man_rush": [
        # carrier already placed; supporting skaters on the rush
        ("trailer", "trailer", 60, -0.4),       # trailer follows on weak side
        ("wide_o", "wing", 70, -1.0),           # wide wing crashing far post
        ("high_f", "wing", 55, 0.2),            # high forward joining late
        ("d1_o", "point", 38, 0.6),             # strong-side D pinching
        ("d2_o", "point", 32, -0.6),            # weak-side D back at blue
    ],
    "east_west_seam": [
        ("netfront", "net_front", 84, 0.15),
        ("weakside", "weak_side", 78, -0.9),
        ("trailer", "trailer", 65, 0.2),
        ("d1_o", "point", 36, 0.5),
        ("d2_o", "point", 33, -0.5),
    ],
    "point_shot_traffic": [
        ("netfront", "net_front", 82, 0.15),
        ("tip", "net_front", 79, -0.15),
        ("strong_wing", "wing", 70, 1.0),
        ("weak_wing", "wing", 70, -1.0),
        ("d2_o", "point", 34, -0.6),  # partner at the other point
    ],
    "oz_cycle_low": [
        ("netfront", "net_front", 84, 0.2),
        ("weakside", "weak_side", 78, -0.8),
        ("highslot", "high_slot", 65, 0.0),
        ("d1_o", "point", 36, 0.6),
        ("d2_o", "point", 33, -0.6),
    ],
    "net_front_chaos": [
        ("netfront", "net_front", 83, 0.1),
        ("weakside", "weak_side", 78, -0.8),
        ("highslot", "high_slot", 64, 0.0),
        ("d1_o", "point", 36, 0.6),
        ("d2_o", "point", 33, -0.6),
    ],
}

DEFENSE_ANCHORS = {
    "odd_man_rush": [
        # backchecking situation — defenders strung out high → low
        ("d1_d", "defender", 78, 0.3),          # near-side D collapsing
        ("d2_d", "defender", 70, -0.4),         # partner sealing weak side
        ("f1_d", "forward", 60, 0.5),           # backchecker on strong side
        ("f2_d", "forward", 52, -0.2),          # mid backchecker
        ("f3_d", "forward", 44, 0.4),           # high backchecker
    ],
    "east_west_seam": [
        ("d1_d", "defender", 84, 0.3),
        ("d2_d", "defender", 84, -0.3),
        ("f1_d", "forward", 72, 0.6),
        ("f2_d", "forward", 70, -0.7),
        ("f3_d", "forward", 62, 0.0),
    ],
    "point_shot_traffic": [
        # box / +1: bodies in front of net plus point pressure
        ("d1_d", "defender", 81, 0.4),
        ("d2_d", "defender", 81, -0.4),
        ("f1_d", "forward", 74, 0.8),
        ("f2_d", "forward", 74, -0.8),
        ("f3_d", "forward", 50, 0.0),           # point pressure
    ],
    "oz_cycle_low": [
        ("d1_d", "defender", 84, 0.4),
        ("d2_d", "defender", 80, -0.5),
        ("f1_d", "forward", 73, 0.7),
        ("f2_d", "forward", 70, -0.8),
        ("f3_d", "forward", 60, 0.0),
    ],
    "net_front_chaos": [
        ("d1_d", "defender", 84, 0.3),
        ("d2_d", "defender", 82, -0.4),
        ("f1_d", "forward", 74, 0.7),
        ("f2_d", "forward", 72, -0.6),
        ("f3_d", "forward", 60, 0.0),
    ],
}


def _stick_alternating(seed: int) -> str:
    return "right" if seed % 2 else "left"


def _build_skaters(
    family: str,
    px: float,
    py: float,
    off_total: int,
    def_total: int,
    hand: str,
) -> list[dict]:
    """Place `off_total - 1` offensive supporters and `def_total` defenders.

    The carrier and goalie are added by the caller. `off_total` includes the
    carrier; `def_total` excludes the goalie.
    """
    side = 1.0 if py >= 0 else -1.0
    skaters: list[dict] = []

    off_anchors = OFFENSE_ANCHORS.get(family, OFFENSE_ANCHORS["net_front_chaos"])
    def_anchors = DEFENSE_ANCHORS.get(family, DEFENSE_ANCHORS["net_front_chaos"])

    # Take as many anchors as we need (clamp to what's defined).
    n_off_supports = max(0, min(len(off_anchors), off_total - 1))
    n_def = max(0, min(len(def_anchors), def_total))

    for i, (label, role, ax, yf) in enumerate(off_anchors[:n_off_supports]):
        x = _clamp_x(ax)
        y = _clamp_y(yf * abs(py) if abs(py) > 1 else yf * 18 * side)
        stick = "right" if hand.upper().startswith("R") else "left"
        # Vary sticks a little so the rink doesn't look mono-handed.
        if i and i % 2 == 0:
            stick = "left" if stick == "right" else "right"
        skaters.append(_sk(label, label.replace("_", " "), "offense", role, x, y, stick))

    for i, (label, role, ax, yf) in enumerate(def_anchors[:n_def]):
        x = _clamp_x(ax)
        y = _clamp_y(yf * abs(py) if abs(py) > 1 else yf * 18 * side)
        skaters.append(_sk(label, label.replace("_", " "), "defense", role, x, y, _stick_alternating(i)))

    return skaters


def _build_scene(
    slug: str,
    title: str,
    family: str,
    manpower: str,
    px: float,
    py: float,
    hand: str,
    off_total: int,
    def_total: int,
) -> dict:
    carrier = _sk(
        "carrier", "carrier", "offense", "carrier",
        px, py,
        "right" if hand.upper().startswith("R") else "left",
    )
    skaters = _build_skaters(family, px, py, off_total, def_total, hand)
    goalie = goalie_on_angle(px, py)
    entities = [carrier, *skaters, goalie]

    return {
        "id": slug,
        "title": title,
        "situation_family": family,
        "manpower": manpower,
        "default_camera": default_camera(family),
        "puck": {"x": round(px, 1), "y": round(py, 1)},
        "entities": entities,
        "overlays": {"royal_road": True, "pass_lanes": []},
        "seed_source": "shot_to_scene_v2",
    }


def scene_from_row(row: dict) -> dict:
    """Build a viewer-ready scene dict from one shot_index row (dict-like)."""
    px = abs(_as_float(row.get("xCordAdjusted"), 72))
    py = _as_float(row.get("yCordAdjusted"), 0)
    hand = _as_str(row.get("shooterLeftRight"), "L")[:1] or "L"
    manpower = _as_str(row.get("manpower"), "5v5")
    family = classify_family({
        "shotRush": row.get("shotRush"),
        "shotDistance": row.get("shotDistance"),
    })
    shooter = _as_str(row.get("shooterName"), "shot") or "shot"
    game_id = _as_str(row.get("game_id"), "")
    shot_id = _as_str(row.get("shotID"), "")
    slug = f"mp-{game_id}-{shot_id}".replace(" ", "-").replace(".", "").lower() or f"mp-{shooter}".lower()
    title = f"{shooter} · {family.replace('_', ' ')} · {manpower}"

    off_f = _as_int(row.get("shootingTeamForwardsOnIce"), 3)
    off_d = _as_int(row.get("shootingTeamDefencemenOnIce"), 2)
    def_f = _as_int(row.get("defendingTeamForwardsOnIce"), 3)
    def_d = _as_int(row.get("defendingTeamDefencemenOnIce"), 2)
    off_total = max(1, off_f + off_d)
    def_total = max(0, def_f + def_d)

    scene = _build_scene(
        slug=slug, title=title, family=family, manpower=manpower,
        px=px, py=py, hand=hand,
        off_total=off_total, def_total=def_total,
    )
    scene["source"] = {
        "provider": "MoneyPuck",
        "season": int(_as_float(row.get("season"), 0)) or None,
        "shot_id": shot_id or None,
        "game_id": game_id or None,
        "shooter": shooter,
        "shooter_hand": hand,
        "shooter_position": _as_str(row.get("playerPositionThatDidEvent")) or None,
        "shot_type": _as_str(row.get("shotType")) or None,
        "shot_distance": _as_float(row.get("shotDistance")) or None,
        "shot_angle": _as_float(row.get("shotAngleAdjusted")) or None,
        "x_goal": _as_float(row.get("xGoal")) or None,
        "last_event": _as_str(row.get("lastEventCategory")) or None,
        "observed_outcome": _as_str(row.get("outcome")) or None,
        "on_ice_offense": {"forwards": off_f, "defensemen": off_d},
        "on_ice_defense": {"forwards": def_f, "defensemen": def_d},
    }
    return scene


def bayes_features(row: dict) -> dict:
    """Extract the keys the Bayesian module needs."""
    gid = row.get("goalieIdForShot")
    if gid is not None and not (isinstance(gid, float) and math.isnan(gid)):
        goalie_id = str(int(float(gid)))
    else:
        goalie_id = None
    return {
        "zone": _as_str(row.get("zone")),
        "manpower": _as_str(row.get("manpower"), "5v5"),
        "hex_cell": _as_str(row.get("hex")) or None,
        "goalie_id": goalie_id,
        "goalie_name": _as_str(row.get("goalieNameForShot")) or None,
    }
