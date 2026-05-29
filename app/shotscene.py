"""Turn a single MoneyPuck shot row into a viewer scene + analysis context.

Reuses scripts/shot_to_scene.py for the per-family skater template (puck,
shooter, supporting cast, goalie-on-angle). Adds the bits needed for the
Bayesian module: zone label, hex cell, manpower, goalie_id.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from shot_to_scene import build_scene, classify_family  # type: ignore  # noqa: E402


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return default
        return float(v)
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
    scene = build_scene(
        scene_id=slug,
        title=title,
        family=family,
        manpower=manpower,
        px=px,
        py=py,
        hand=hand,
    )
    # Annotate with source metadata so the analyzer/UI can show provenance.
    scene["source"] = {
        "provider": "MoneyPuck",
        "season": int(_as_float(row.get("season"), 0)) or None,
        "shot_id": shot_id or None,
        "game_id": game_id or None,
        "shooter": shooter,
        "shooter_hand": hand,
        "shot_type": _as_str(row.get("shotType")) or None,
        "shot_distance": _as_float(row.get("shotDistance")) or None,
        "shot_angle": _as_float(row.get("shotAngleAdjusted")) or None,
        "x_goal": _as_float(row.get("xGoal")) or None,
        "last_event": _as_str(row.get("lastEventCategory")) or None,
        "observed_outcome": _as_str(row.get("outcome")) or None,
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
