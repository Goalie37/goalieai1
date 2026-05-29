#!/usr/bin/env python3
"""Build Dirichlet priors + slim shot index from a MoneyPuck shot-level CSV.

Inputs:
    data/moneypuck/shots_2018-2024.csv  (or any file matching shots_*.csv)

Outputs:
    data/derived/priors.json        league + per-goalie Dirichlet counts
    data/derived/shots_index.parquet slim per-shot table used for random sampling

The 5 outcomes (mutually exclusive, ~98% coverage):
    goal | rebound | freeze | play_in_zone | play_out_zone

Buckets:
    - zone bin (named, for LLM narration)
    - hex cell (5ft grid in offensive zone, for heatmap)
    Both conditioned on manpower (5v5 / 5v4 / 4v5 / other).
    Per-goalie counts are stored by (zone, manpower) only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "moneypuck" / "shots_2018-2024.csv"
OUT_DIR = REPO / "data" / "derived"
PRIORS_OUT = OUT_DIR / "priors.json"
INDEX_OUT = OUT_DIR / "shots_index.parquet"

OUTCOMES = ["goal", "rebound", "freeze", "play_in_zone", "play_out_zone"]

HEX_X_MIN, HEX_X_MAX = 25, 100
HEX_Y_MIN, HEX_Y_MAX = -42, 43
HEX_SIZE = 5

USECOLS = [
    "shotID", "season", "game_id", "team", "isHomeTeam",
    "xCordAdjusted", "yCordAdjusted", "shotDistance", "shotAngleAdjusted",
    "shotType", "shotRush", "shotRebound", "lastEventCategory",
    "homeSkatersOnIce", "awaySkatersOnIce",
    "shootingTeamForwardsOnIce", "shootingTeamDefencemenOnIce",
    "defendingTeamForwardsOnIce", "defendingTeamDefencemenOnIce",
    "goalieIdForShot", "goalieNameForShot",
    "shooterPlayerId", "shooterName", "shooterLeftRight",
    "playerPositionThatDidEvent",
    "xGoal", "xRebound", "xFroze",
    "goal", "shotGeneratedRebound", "shotGoalieFroze",
    "shotPlayContinuedInZone", "shotPlayContinuedOutsideZone",
    "shotWasOnGoal",
]


def zone_of(x: float, y: float) -> str:
    """Named zone bin used for LLM narration. Coords: attacking net at +89."""
    ay = abs(y)
    if x >= 89:
        return "behind_net"
    if x >= 75 and ay < 11:
        return "low_slot"
    if x >= 65 and ay < 12:
        return "mid_slot"
    if x >= 55 and ay < 12:
        return "high_slot"
    if x >= 65 and ay <= 30:
        return "circle_left" if y > 0 else "circle_right"
    if x >= 55 and ay > 30:
        return "wing_left" if y > 0 else "wing_right"
    if x < 55 and ay < 18:
        return "point_center"
    if x < 55:
        return "point_left" if y > 0 else "point_right"
    return "perimeter"


def manpower_label(home_sk: int, away_sk: int, is_home: float) -> str:
    if is_home == 1:
        atk, dfn = home_sk, away_sk
    else:
        atk, dfn = away_sk, home_sk
    if atk == dfn == 5:
        return "5v5"
    if atk == 5 and dfn == 4:
        return "5v4"
    if atk == 4 and dfn == 5:
        return "4v5"
    if atk == dfn == 4:
        return "4v4"
    if atk == 6 or dfn == 6:
        return "empty_net"
    return f"{atk}v{dfn}"


def hex_id(x: float, y: float) -> str:
    cx = int((x - HEX_X_MIN) // HEX_SIZE)
    cy = int((y - HEX_Y_MIN) // HEX_SIZE)
    return f"h{cx}_{cy}"


def categorical_outcome(row) -> str:
    if row["goal"] == 1:
        return "goal"
    if row["shotGeneratedRebound"] == 1:
        return "rebound"
    if row["shotGoalieFroze"] == 1:
        return "freeze"
    if row["shotPlayContinuedInZone"] == 1:
        return "play_in_zone"
    if row["shotPlayContinuedOutsideZone"] == 1:
        return "play_out_zone"
    return "other"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Reading {SRC} …")
    df = pd.read_csv(SRC, usecols=USECOLS, low_memory=False)
    print(f"  loaded {len(df):,} rows")

    df = df.dropna(subset=["xCordAdjusted", "yCordAdjusted"])
    for col in [
        "goal", "shotGeneratedRebound", "shotGoalieFroze",
        "shotPlayContinuedInZone", "shotPlayContinuedOutsideZone",
    ]:
        df[col] = df[col].fillna(0).astype(int)

    df["outcome"] = df.apply(categorical_outcome, axis=1)
    df = df[df["outcome"] != "other"].copy()
    print(f"  {len(df):,} rows after dropping ambiguous outcomes")

    df["x_abs"] = df["xCordAdjusted"].abs()
    df["zone"] = [zone_of(x, y) for x, y in zip(df["x_abs"], df["yCordAdjusted"])]
    df["hex"] = [hex_id(x, y) for x, y in zip(df["x_abs"], df["yCordAdjusted"])]
    df["manpower"] = [
        manpower_label(h, a, ih)
        for h, a, ih in zip(
            df["homeSkatersOnIce"].fillna(5).astype(int),
            df["awaySkatersOnIce"].fillna(5).astype(int),
            df["isHomeTeam"].fillna(1),
        )
    ]

    def count_vec(g: pd.DataFrame) -> list[int]:
        c = g["outcome"].value_counts()
        return [int(c.get(o, 0)) for o in OUTCOMES]

    print("Bucketing league by zone × manpower …")
    league_zone = {}
    for (zone, mp), g in df.groupby(["zone", "manpower"], observed=True):
        if len(g) < 30:
            continue
        league_zone[f"{zone}|{mp}"] = {
            "n": int(len(g)),
            "counts": count_vec(g),
            "xg_mean": float(g["xGoal"].mean()),
        }

    print("Bucketing league by hex × manpower …")
    league_hex = {}
    for (hx, mp), g in df.groupby(["hex", "manpower"], observed=True):
        if len(g) < 20:
            continue
        league_hex[f"{hx}|{mp}"] = {
            "n": int(len(g)),
            "counts": count_vec(g),
            "xg_mean": float(g["xGoal"].mean()),
        }

    print("Per-goalie counts (zone × manpower) …")
    goalies = {}
    df_g = df.dropna(subset=["goalieIdForShot"])
    for gid, gdf in df_g.groupby("goalieIdForShot"):
        if len(gdf) < 200:
            continue
        name = gdf["goalieNameForShot"].mode().iloc[0] if not gdf["goalieNameForShot"].mode().empty else ""
        buckets = {}
        for (zone, mp), g in gdf.groupby(["zone", "manpower"], observed=True):
            if len(g) < 10:
                continue
            buckets[f"{zone}|{mp}"] = {"n": int(len(g)), "counts": count_vec(g)}
        if buckets:
            goalies[str(int(gid))] = {"name": str(name), "n": int(len(gdf)), "buckets": buckets}

    priors = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "MoneyPuck.com shots_2018-2024.csv",
        "rows_aggregated": int(len(df)),
        "seasons": sorted(int(s) for s in df["season"].unique()),
        "outcomes": OUTCOMES,
        "hex_grid": {
            "x_min": HEX_X_MIN, "x_max": HEX_X_MAX,
            "y_min": HEX_Y_MIN, "y_max": HEX_Y_MAX,
            "cell_size": HEX_SIZE,
        },
        "league_zone": league_zone,
        "league_hex": league_hex,
        "goalies": goalies,
    }
    PRIORS_OUT.write_text(json.dumps(priors, indent=1))
    print(f"Wrote {PRIORS_OUT} ({PRIORS_OUT.stat().st_size / 1e6:.1f} MB)")

    print("Writing slim shot index …")
    keep = [
        "shotID", "season", "game_id", "team", "isHomeTeam",
        "xCordAdjusted", "yCordAdjusted", "shotDistance", "shotAngleAdjusted",
        "shotType", "shotRush", "shotRebound", "lastEventCategory",
        "homeSkatersOnIce", "awaySkatersOnIce",
        "shootingTeamForwardsOnIce", "shootingTeamDefencemenOnIce",
        "defendingTeamForwardsOnIce", "defendingTeamDefencemenOnIce",
        "goalieIdForShot", "goalieNameForShot",
        "shooterPlayerId", "shooterName", "shooterLeftRight",
        "playerPositionThatDidEvent",
        "xGoal", "outcome", "zone", "hex", "manpower",
    ]
    slim = df[keep].copy()
    slim.to_parquet(INDEX_OUT, index=False, compression="zstd")
    print(f"Wrote {INDEX_OUT} ({INDEX_OUT.stat().st_size / 1e6:.1f} MB, {len(slim):,} rows)")


if __name__ == "__main__":
    main()
