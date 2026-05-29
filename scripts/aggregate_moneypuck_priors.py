#!/usr/bin/env python3
"""
Aggregate MoneyPuck CSVs into GoalieAI prior buckets.

Supports:
  - Shot-level CSVs (xGoals, rush, distance) — best for situation buckets
  - Goalie season summary CSVs (goalies_*.csv) — league rates by manpower + danger tier

Usage:
  python3 scripts/aggregate_moneypuck_priors.py --input data/moneypuck/
  python3 scripts/aggregate_moneypuck_priors.py --input data/moneypuck/raw/shots.csv

Credit MoneyPuck.com — https://moneypuck.com/data.htm
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "knowledge" / "moneypuck_priors.json"

COL_XG = ("xGoals", "xGoal", "expectedGoals")
COL_GOAL = ("isGoal", "goal", "Goal")
COL_REBOUND = ("xRebound", "reboundGoal", "xGoals_rebound")
COL_FREEZE = ("xFreeze", "freezeGoal")
COL_RUSH = ("isRushShot", "rushShot", "shotRush")
COL_REBOUND_SHOT = ("shotRebound", "isRebound", "reboundShot")
COL_DISTANCE = ("shotDistance", "arenaAdjustedShotDistance")

SITUATION_MAP = {
    "5on5": "5v5",
    "5on4": "5v4",
    "4on5": "4v5",
}


def pick_col(header: set[str], candidates: tuple[str, ...]) -> str | None:
    for c in candidates:
        if c in header:
            return c
    return None


def safe_float(val: str | None) -> float:
    if val is None or val == "":
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0


def band_from_rate(rate: float) -> str:
    if rate >= 0.12:
        return "high"
    if rate >= 0.06:
        return "medium"
    return "low"


def is_goalie_season_csv(header: set[str]) -> bool:
    return "playerId" in header and "unblocked_shot_attempts" in header and "situation" in header


def aggregate_goalie_season(rows: list[dict]) -> dict:
    """Sum goalie-season rows by situation; derive league rates."""
    by_sit: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for row in rows:
        sit = row.get("situation", "")
        if sit in ("all", "other"):
            continue
        agg = by_sit[sit]
        agg["shots"] += safe_float(row.get("unblocked_shot_attempts"))
        agg["goals"] += safe_float(row.get("goals"))
        agg["xgoals"] += safe_float(row.get("xGoals"))
        agg["rebounds"] += safe_float(row.get("rebounds"))
        agg["xrebounds"] += safe_float(row.get("xRebounds"))
        agg["freeze"] += safe_float(row.get("freeze"))
        agg["xfreeze"] += safe_float(row.get("xFreeze"))
        agg["ongoal"] += safe_float(row.get("ongoal"))
        agg["high_shots"] += safe_float(row.get("highDangerShots"))
        agg["high_goals"] += safe_float(row.get("highDangerGoals"))
        agg["med_shots"] += safe_float(row.get("mediumDangerShots"))
        agg["med_goals"] += safe_float(row.get("mediumDangerGoals"))
        agg["low_shots"] += safe_float(row.get("lowDangerShots"))
        agg["low_goals"] += safe_float(row.get("lowDangerGoals"))
        agg["rows"] += 1

    def rate(num: float, den: float) -> float:
        return num / den if den > 0 else 0.0

    def bucket_from_sit(sit_key: str, playbook_id: str, danger: str | None = None) -> dict | None:
        if sit_key not in by_sit:
            return None
        a = by_sit[sit_key]
        mp = SITUATION_MAP.get(sit_key, "5v5")
        if danger == "high":
            shots, goals, xg = a["high_shots"], a["high_goals"], a.get("high_xg", 0)
            xg = sum(safe_float(r.get("highDangerxGoals")) for r in rows if r.get("situation") == sit_key)
        elif danger == "medium":
            shots, goals = a["med_shots"], a["med_goals"]
            xg = sum(safe_float(r.get("mediumDangerxGoals")) for r in rows if r.get("situation") == sit_key)
        elif danger == "low":
            shots, goals = a["low_shots"], a["low_goals"]
            xg = sum(safe_float(r.get("lowDangerxGoals")) for r in rows if r.get("situation") == sit_key)
        else:
            shots, goals, xg = a["shots"], a["goals"], a["xgoals"]

        if shots < 1000:
            return None

        p_goal = rate(goals, shots)
        p_xg = rate(xg, shots)
        p_reb = rate(a["rebounds"], a["ongoal"]) if a["ongoal"] else rate(a["rebounds"], shots)
        p_freeze = rate(a["freeze"], a["ongoal"]) if a["ongoal"] else 0.0

        if danger:
            bid = f"{playbook_id}_{mp}"
        elif playbook_id in ("league_5v5", "league_powerplay", "league_penalty_kill"):
            bid = playbook_id
        else:
            bid = f"{playbook_id}_{mp}"
        label_suffix = f" ({danger} danger)" if danger else ""

        return {
            "bucket_id": bid,
            "shot_count": int(shots),
            "goalie_season_rows": int(a["rows"]),
            "manpower": mp,
            "p_goal_empirical": round(p_goal, 4),
            "p_goal_xg_mean": round(p_xg, 4),
            "p_rebound_mean": round(p_reb, 4),
            "p_freeze_mean": round(p_freeze, 4),
            "data_granularity": "goalie_season_summary",
            "branches": [
                {
                    "branch_id": "shot_branch",
                    "label": f"Shot on net{label_suffix}",
                    "prior_band": band_from_rate(p_xg or p_goal),
                },
                {
                    "branch_id": "rebound_branch",
                    "label": "Rebound after save",
                    "prior_band": band_from_rate(p_reb),
                },
                {
                    "branch_id": "freeze_branch",
                    "label": "Freeze / play stopped",
                    "prior_band": band_from_rate(p_freeze),
                },
            ],
        }

    out = []
    specs = [
        ("5on5", "league_5v5", None),
        ("5on4", "league_powerplay", None),
        ("4on5", "league_penalty_kill", None),
        ("5on5", "slot_seam", "high"),
        ("5on5", "point_shot_traffic", "low"),
        ("5on5", "medium_danger", "medium"),
    ]
    for sit, pid, danger in specs:
        b = bucket_from_sit(sit, pid, danger)
        if b:
            out.append(b)

    playbook_aliases = [
        {
            "bucket_id": "odd_man_rush_5v5",
            "derived_from": "medium_danger_5v5",
            "note": "Proxy: no rush flag in goalie season data; uses 5v5 medium-danger rates.",
        },
        {
            "bucket_id": "slot_seam_5v5",
            "derived_from": "slot_seam_5v5",
            "note": "Proxy: high-danger 5v5 shots approximate slot/seam finishing.",
        },
        {
            "bucket_id": "net_front_rebound_5v5",
            "derived_from": "league_5v5",
            "note": "Uses overall 5v5 rebound rate.",
        },
        {
            "bucket_id": "point_shot_traffic_5v5",
            "derived_from": "point_shot_traffic_5v5",
            "note": "Proxy: low-danger 5v5 shots approximate point-volume shooting.",
        },
    ]

    by_id = {b["bucket_id"]: b for b in out}
    for alias in playbook_aliases:
        if alias["bucket_id"] in by_id:
            continue
        src = by_id.get(alias["derived_from"])
        if not src:
            continue
        copy = {k: v for k, v in src.items() if k != "bucket_id"}
        copy["bucket_id"] = alias["bucket_id"]
        copy["derived_from"] = alias["derived_from"]
        copy["note"] = alias["note"]
        out.append(copy)
        by_id[alias["bucket_id"]] = copy

    return {"buckets": out}


def manpower_key(row: dict) -> str:
    sit = str(row.get("situation") or row.get("strength") or "").lower()
    if "5on4" in sit or "5v4" in sit:
        return "5v4"
    if "4on5" in sit or "4v5" in sit:
        return "4v5"
    return "5v5"


def classify_bucket(row: dict, cols: dict) -> str:
    rush_col = cols.get("rush")
    reb_col = cols.get("rebound_shot")
    dist_col = cols.get("distance")
    is_rush = rush_col and str(row.get(rush_col, "")).lower() in ("1", "true", "yes")
    is_rebound = reb_col and str(row.get(reb_col, "")).lower() in ("1", "true", "yes")
    dist = safe_float(row.get(dist_col)) if dist_col else None
    if is_rush:
        return "odd_man_rush"
    if is_rebound and dist and dist < 25:
        return "net_front_rebound"
    if dist:
        if dist >= 50:
            return "point_shot_traffic"
        if 20 <= dist < 35:
            return "slot_seam"
        if dist < 15:
            return "wrap_low"
    return "all_shots"


def aggregate_shot_rows(rows: list[dict], cols: dict) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        base = classify_bucket(row, cols)
        mp = manpower_key(row)
        buckets[f"{base}_{mp}"].append(row)

    out_buckets = []
    xg_col, goal_col = cols.get("xg"), cols.get("goal")
    reb_col, freeze_col = cols.get("rebound"), cols.get("freeze")

    for bucket_id, subset in sorted(buckets.items()):
        if len(subset) < 100:
            continue
        xgs, rebounds, freezes, goals = [], [], [], 0
        for r in subset:
            if xg_col:
                v = safe_float(r.get(xg_col))
                if v:
                    xgs.append(v)
            if goal_col and str(r.get(goal_col, "")).lower() in ("1", "true", "yes"):
                goals += 1
            if reb_col:
                v = safe_float(r.get(reb_col))
                if v:
                    rebounds.append(v)
            if freeze_col:
                v = safe_float(r.get(freeze_col))
                if v:
                    freezes.append(v)

        n = len(subset)
        p_xg = sum(xgs) / len(xgs) if xgs else goals / n
        p_reb = sum(rebounds) / len(rebounds) if rebounds else 0.15
        out_buckets.append({
            "bucket_id": bucket_id,
            "shot_count": n,
            "data_granularity": "shot_level",
            "p_goal_empirical": round(goals / n, 4) if goal_col else None,
            "p_goal_xg_mean": round(p_xg, 4),
            "p_rebound_mean": round(p_reb, 4),
            "p_freeze_mean": round(sum(freezes) / len(freezes), 4) if freezes else None,
            "branches": [
                {"branch_id": "shot_branch", "label": "Shot on net", "prior_band": band_from_rate(p_xg)},
                {"branch_id": "rebound_branch", "label": "Rebound chance", "prior_band": band_from_rate(p_reb)},
            ],
        })

    return {"buckets": out_buckets}


def detect_columns(header: list[str]) -> dict:
    h = set(header)
    return {
        "xg": pick_col(h, COL_XG),
        "goal": pick_col(h, COL_GOAL),
        "rebound": pick_col(h, COL_REBOUND),
        "freeze": pick_col(h, COL_FREEZE),
        "rush": pick_col(h, COL_RUSH),
        "rebound_shot": pick_col(h, COL_REBOUND_SHOT),
        "distance": pick_col(h, COL_DISTANCE),
    }


def load_csv(path: Path) -> tuple[list[dict], dict, str]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        rows = list(reader)
    if is_goalie_season_csv(header):
        return rows, {}, "goalie_season"
    return rows, detect_columns(header), "shot"


def write_defaults(output: Path) -> None:
    payload = {
        "source_url": "https://moneypuck.com/data.htm",
        "credited_to": "MoneyPuck.com",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prior_source": "playbook_default",
        "disclaimer": "Place MoneyPuck CSV in data/moneypuck/ and re-run script.",
        "buckets": [],
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote empty defaults to {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/moneypuck")
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    inp = Path(args.input)
    files = sorted(inp.glob("*.csv")) if inp.is_dir() else [inp]
    files = [f for f in files if f.exists()]

    if not files:
        write_defaults(Path(args.output))
        return

    all_shot_rows: list[dict] = []
    all_goalie_rows: list[dict] = []
    cols: dict = {}
    types: set[str] = set()

    for f in files:
        rows, c, kind = load_csv(f)
        types.add(kind)
        if kind == "goalie_season":
            all_goalie_rows.extend(rows)
            print(f"Loaded {len(rows)} goalie-season rows from {f.name}")
        else:
            all_shot_rows.extend(rows)
            cols = {k: v or cols.get(k) for k, v in c.items()}
            print(f"Loaded {len(rows)} shot rows from {f.name}")

    if all_goalie_rows and not all_shot_rows:
        agg = aggregate_goalie_season(all_goalie_rows)
        data_type = "goalie_season_summary"
        row_count = len(all_goalie_rows)
    elif all_shot_rows:
        agg = aggregate_shot_rows(all_shot_rows, cols)
        data_type = "shot_level"
        row_count = len(all_shot_rows)
    else:
        write_defaults(Path(args.output))
        return

    payload = {
        "source_url": "https://moneypuck.com/data.htm",
        "credited_to": "MoneyPuck.com",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_files": [f.name for f in files],
        "data_type": data_type,
        "rows_aggregated": row_count,
        "prior_source": "moneypuck",
        "disclaimer": "League priors for similar situations — not exact xG for a still image.",
        **agg,
    }
    if data_type == "goalie_season_summary":
        payload["note"] = (
            "Aggregated from goalie season CSV. For rush/seam/location buckets, add shot-level CSV from data.htm."
        )

    out = Path(args.output)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(agg['buckets'])} buckets, {data_type})")


if __name__ == "__main__":
    main()
