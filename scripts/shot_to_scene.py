#!/usr/bin/env python3
"""
Seed a GoalieAI viewer scene from a shot location.

The shot is only the SEED: it fixes the puck and the goalie's angle on the net.
Supporting skaters are placed by a situation-family template, then the user
drags them into place in the 3D viewer.

Coordinate system (matches MoneyPuck shot data, feet):
  x  north-south, attacking net at x = +89, blue line at x = +25
  y  east-west, center ice y = 0, boards at y = +/-42.5

Inputs:
  A) Explicit shot location (works without any CSV):
       python3 scripts/shot_to_scene.py --x 72 --y -16 \
           --family east_west_seam --manpower 5v4 --hand R --out viewer/scenes/seam.json

  B) A MoneyPuck shot-level CSV row (the file with xCordAdjusted / yCordAdjusted;
     download from https://moneypuck.com/data.htm -> Shot Data):
       python3 scripts/shot_to_scene.py --csv data/moneypuck/raw/shots_2024.csv --row 0

Credit MoneyPuck.com for any data used.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

NET_X = 89.0
NET_Y = 0.0
CREASE_DEPTH = 3.5  # how far the goalie sits off the goal line, on the angle

# Supporting-skater templates, expressed as offsets/anchors in rink feet.
# Each entry: (id, label, team, role, x, y, stick) where x/y may reference the
# puck via a callable. Kept deliberately simple — the user fine-tunes by drag.
def template(family: str, px: float, py: float, hand: str) -> list[dict]:
    side = 1 if py >= 0 else -1
    stick = "right" if hand.upper().startswith("R") else "left"
    if family == "odd_man_rush":
        return [
            _sk("trailer", "trailer", "offense", "trailer", px - 12, py * 0.4, stick),
            _sk("backchecker", "D (back)", "defense", "defender", (px + NET_X) / 2, py * 0.5, "right"),
        ]
    if family == "east_west_seam":
        return [
            _sk("shooter", "one-timer", "offense", "shooter", px + 2, -py, stick),
            _sk("netfront", "net-front", "offense", "net_front", 83, 2, "left"),
            _sk("point", "point", "offense", "point", 40, py * 0.5, "left"),
        ]
    if family == "point_shot_traffic":
        return [
            _sk("screen1", "screen", "offense", "net_front", 82, 1, "left"),
            _sk("screen2", "tip", "offense", "net_front", 79, -3, "right"),
            _sk("defender", "D (box)", "defense", "defender", 81, -1, "left"),
        ]
    if family == "oz_cycle_low":
        return [
            _sk("netfront", "net-front", "offense", "net_front", 84, 4 * side, "right"),
            _sk("weakside", "weak-side", "offense", "weak_side", 78, -16 * side, stick),
        ]
    # net_front_chaos / default
    return [
        _sk("netfront", "net-front", "offense", "net_front", 83, 2, "left"),
        _sk("weakside", "weak-side", "offense", "weak_side", 78, -15, stick),
    ]


def _sk(eid, label, team, role, x, y, stick):
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


def facing_toward_net(x: float, y: float) -> int:
    return int(round(math.degrees(math.atan2(NET_Y - y, NET_X - x))))


def goalie_on_angle(px: float, py: float) -> dict:
    dx, dy = px - NET_X, py - NET_Y
    dist = math.hypot(dx, dy) or 1.0
    gx = NET_X + dx / dist * CREASE_DEPTH
    gy = NET_Y + dy / dist * CREASE_DEPTH
    return {
        "id": "goalie",
        "label": "goalie",
        "team": "goalie",
        "role": "goalie",
        "x": round(gx, 1),
        "y": round(gy, 1),
        "facing": facing_toward_net(px, py),
    }


def default_camera(family: str) -> str:
    return {
        "oz_cycle_low": "behind_net",
        "east_west_seam": "goalie_pov",
    }.get(family, "broadcast")


def build_scene(scene_id, title, family, manpower, px, py, hand, pass_to=None):
    skaters = template(family, px, py, hand)
    carrier = _sk("carrier", "carrier", "offense", "carrier", px, py, "right" if hand.upper().startswith("R") else "left")
    entities = [carrier, *skaters, goalie_on_angle(px, py)]
    lanes = []
    if pass_to:
        lanes = [["carrier", pass_to]]
    elif family == "east_west_seam":
        lanes = [["carrier", "shooter"]]
    elif family == "oz_cycle_low":
        lanes = [["carrier", "netfront"]]
    return {
        "id": scene_id,
        "title": title,
        "situation_family": family,
        "manpower": manpower,
        "default_camera": default_camera(family),
        "puck": {"x": round(px, 1), "y": round(py, 1)},
        "entities": entities,
        "overlays": {"royal_road": True, "pass_lanes": lanes},
        "seed_source": "shot_to_scene",
    }


def classify_family(row: dict) -> str:
    def f(*names):
        for n in names:
            if n in row and row[n] not in ("", None):
                return row[n]
        return ""

    if str(f("shotRush", "isRushShot")).lower() in ("1", "true"):
        return "odd_man_rush"
    dist = f("shotDistance", "arenaAdjustedShotDistance")
    try:
        d = float(dist)
    except (TypeError, ValueError):
        d = 30.0
    if d >= 50:
        return "point_shot_traffic"
    if d < 12:
        return "oz_cycle_low"
    if d < 30:
        return "east_west_seam"
    return "net_front_chaos"


def from_csv_row(path: Path, row_idx: int) -> dict:
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        rows = list(csv.DictReader(fh))
    row = rows[row_idx]

    def g(*names, default=None):
        for n in names:
            if n in row and row[n] not in ("", None):
                return row[n]
        return default

    px = float(g("xCordAdjusted", "arenaAdjustedXCord", "xCord", default=72))
    py = float(g("yCordAdjusted", "arenaAdjustedYCord", "yCord", default=0))
    px = abs(px)  # adjusted coords keep attacking end positive
    hand = g("shooterLeftRight", default="L") or "L"
    home = g("homeSkatersOnIce", default="5")
    away = g("awaySkatersOnIce", default="5")
    is_home = str(g("isHomeTeam", "team", default="")).lower() in ("1", "true", "home")
    atk, dfn = (home, away) if is_home else (away, home)
    manpower = f"{atk}v{dfn}" if atk and dfn else "5v5"
    family = classify_family(row)
    shooter = g("shooterName", default="shot")
    scene_id = f"mp-{g('game_id', default='shot')}-{row_idx}".replace(" ", "-").lower()
    title = f"MoneyPuck seed — {shooter} ({family})"
    return build_scene(scene_id, title, family, manpower, px, py, hand[0])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", help="MoneyPuck shot-level CSV (with xCordAdjusted/yCordAdjusted)")
    p.add_argument("--row", type=int, default=0, help="Row index when using --csv")
    p.add_argument("--x", type=float, help="Puck rink x (attacking net at 89)")
    p.add_argument("--y", type=float, help="Puck rink y (center ice 0)")
    p.add_argument("--family", default="net_front_chaos",
                   help="situation family: odd_man_rush | east_west_seam | point_shot_traffic | oz_cycle_low | net_front_chaos")
    p.add_argument("--manpower", default="5v5")
    p.add_argument("--hand", default="L", help="Shooter handedness L|R")
    p.add_argument("--id", default="custom-scene")
    p.add_argument("--title", default="Custom seeded scene")
    p.add_argument("--pass-to", help="Entity id to draw a pass lane to from the carrier")
    p.add_argument("--out", help="Write to this path; otherwise prints to stdout")
    args = p.parse_args()

    if args.csv:
        scene = from_csv_row(Path(args.csv), args.row)
    elif args.x is not None and args.y is not None:
        scene = build_scene(args.id, args.title, args.family, args.manpower,
                            args.x, args.y, args.hand, args.pass_to)
    else:
        p.error("Provide either --csv (+--row) or --x and --y.")

    text = json.dumps(scene, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
