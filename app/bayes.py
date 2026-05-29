"""Bayesian posterior over shot outcomes for the coach analysis.

Model
-----
For a given (zone, manpower) bucket, the league counts over the 5 outcomes
parameterize a Dirichlet prior. Per-goalie observed counts in the same bucket
are added as evidence. The posterior is also Dirichlet; the marginal of each
outcome is Beta(α_i, α_total − α_i), which gives a closed-form mean and a
credible interval per outcome.

The league prior is *weighted* (not used at full count) so a goalie with
hundreds of observations in a bucket actually moves the posterior. The
default effective weight is 60 "league shots" worth — small enough that
goalies dominate when they have ≥200 shots in a bucket, large enough that
sparse buckets fall back to league.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from scipy.stats import beta as beta_dist  # type: ignore

REPO = Path(__file__).resolve().parents[1]
PRIORS_PATH = REPO / "data" / "derived" / "priors.json"

OUTCOMES = ["goal", "rebound", "freeze", "play_in_zone", "play_out_zone"]
OUTCOME_LABELS = {
    "goal": "Goal",
    "rebound": "Rebound",
    "freeze": "Freeze / whistle",
    "play_in_zone": "Play continues in zone",
    "play_out_zone": "Play exits zone",
}
LEAGUE_PRIOR_WEIGHT = 60.0  # effective pseudocount applied to league proportions
SMOOTHING = 0.5  # Laplace-style floor so no outcome has α=0


@dataclass
class PosteriorRow:
    outcome: str
    label: str
    mean: float
    lo: float
    hi: float
    league_mean: float


@dataclass
class Posterior:
    zone: str
    manpower: str
    hex_cell: Optional[str]
    league_n: int
    league_xg_mean: Optional[float]
    goalie_id: Optional[str]
    goalie_name: Optional[str]
    goalie_n_bucket: int
    goalie_n_total: int
    rows: list[PosteriorRow]
    method: str

    def to_dict(self) -> dict:
        return {
            "zone": self.zone,
            "manpower": self.manpower,
            "hex_cell": self.hex_cell,
            "league_n": self.league_n,
            "league_xg_mean": self.league_xg_mean,
            "goalie_id": self.goalie_id,
            "goalie_name": self.goalie_name,
            "goalie_n_bucket": self.goalie_n_bucket,
            "goalie_n_total": self.goalie_n_total,
            "method": self.method,
            "rows": [r.__dict__ for r in self.rows],
        }


@lru_cache(maxsize=1)
def _priors() -> dict:
    if not PRIORS_PATH.exists():
        raise FileNotFoundError(
            f"Missing {PRIORS_PATH}. Run `python3 scripts/build_priors.py` first."
        )
    return json.loads(PRIORS_PATH.read_text())


def hex_grid_meta() -> dict:
    return _priors()["hex_grid"]


def hex_xg_map() -> dict[str, dict]:
    """Public hex-cell xG map (for the rink heatmap UI). Keys: 'h{cx}_{cy}' → {xg, n} averaged across manpower."""
    by_hex: dict[str, dict] = {}
    for key, bucket in _priors()["league_hex"].items():
        hx, _ = key.split("|", 1)
        agg = by_hex.setdefault(hx, {"n": 0, "xg_sum": 0.0})
        agg["n"] += bucket["n"]
        agg["xg_sum"] += bucket["xg_mean"] * bucket["n"]
    return {hx: {"n": v["n"], "xg": v["xg_sum"] / v["n"]} for hx, v in by_hex.items() if v["n"] > 0}


def _league_counts(zone: str, manpower: str) -> tuple[list[float], int, Optional[float]]:
    p = _priors()
    key = f"{zone}|{manpower}"
    bucket = p["league_zone"].get(key)
    if bucket is None:
        # Fall back to 5v5 if rare manpower bucket is empty
        bucket = p["league_zone"].get(f"{zone}|5v5")
    if bucket is None:
        # Last resort: aggregate the whole zone across all manpowers
        agg = [0.0] * len(OUTCOMES)
        n = 0
        xg_n = 0.0
        for k, b in p["league_zone"].items():
            if k.startswith(zone + "|"):
                for i, c in enumerate(b["counts"]):
                    agg[i] += c
                n += b["n"]
                xg_n += b["xg_mean"] * b["n"]
        return agg, n, (xg_n / n if n else None)
    return [float(c) for c in bucket["counts"]], bucket["n"], bucket["xg_mean"]


def _goalie_counts(goalie_id: Optional[str], zone: str, manpower: str) -> tuple[list[float], int, int, Optional[str]]:
    if not goalie_id:
        return [0.0] * len(OUTCOMES), 0, 0, None
    p = _priors()
    g = p["goalies"].get(str(goalie_id))
    if g is None:
        return [0.0] * len(OUTCOMES), 0, 0, None
    bucket = g["buckets"].get(f"{zone}|{manpower}")
    if bucket is None:
        return [0.0] * len(OUTCOMES), 0, g.get("n", 0), g.get("name")
    return [float(c) for c in bucket["counts"]], int(bucket["n"]), int(g.get("n", 0)), g.get("name")


def posterior(
    zone: str,
    manpower: str,
    hex_cell: Optional[str] = None,
    goalie_id: Optional[str] = None,
) -> Posterior:
    league_counts, league_n, league_xg = _league_counts(zone, manpower)
    g_counts, g_n_bucket, g_n_total, g_name = _goalie_counts(goalie_id, zone, manpower)

    league_total = sum(league_counts) or 1.0
    league_props = [c / league_total for c in league_counts]
    league_means = league_props

    if g_n_bucket > 0:
        # Bayesian update: small league-derived prior + goalie observations
        alpha_prior = [LEAGUE_PRIOR_WEIGHT * p + SMOOTHING for p in league_props]
        alpha_post = [a + c for a, c in zip(alpha_prior, g_counts)]
    else:
        # No goalie data: posterior == league rate with uncertainty from N shots
        alpha_post = [c + SMOOTHING for c in league_counts]
    total = sum(alpha_post)

    rows: list[PosteriorRow] = []
    for i, name in enumerate(OUTCOMES):
        a = alpha_post[i]
        b = total - a
        mean = a / total
        lo, hi = beta_dist.ppf([0.05, 0.95], a, b)
        if math.isnan(lo):
            lo = 0.0
        if math.isnan(hi):
            hi = 1.0
        rows.append(PosteriorRow(
            outcome=name,
            label=OUTCOME_LABELS[name],
            mean=float(mean),
            lo=float(lo),
            hi=float(hi),
            league_mean=float(league_means[i]),
        ))

    if g_n_bucket > 0:
        method = (
            f"Dirichlet(α = {LEAGUE_PRIOR_WEIGHT:.0f} · league proportions) "
            f"updated with {g_n_bucket} observed shots from goalie."
        )
    elif goalie_id and g_name:
        method = (
            f"Dirichlet from league proportions in this bucket; no shots on file "
            f"for {g_name} at ({zone}, {manpower}) — falling back to league."
        )
    else:
        method = "Dirichlet from league counts in this bucket (no goalie specified)."

    return Posterior(
        zone=zone,
        manpower=manpower,
        hex_cell=hex_cell,
        league_n=league_n,
        league_xg_mean=league_xg,
        goalie_id=str(goalie_id) if goalie_id else None,
        goalie_name=g_name,
        goalie_n_bucket=g_n_bucket,
        goalie_n_total=g_n_total,
        rows=rows,
        method=method,
    )


def evidence_markdown(post: Posterior) -> str:
    """Compact text representation for injection into the LLM system prompt."""
    lines = [
        "## Bayesian evidence (computed from MoneyPuck 2018–2024)",
        f"- Zone: **{post.zone}**, manpower: **{post.manpower}**"
        + (f", hex cell: `{post.hex_cell}`" if post.hex_cell else ""),
        f"- League sample size for this bucket: {post.league_n:,} shots"
        + (f"; mean xG {post.league_xg_mean:.3f}" if post.league_xg_mean is not None else ""),
    ]
    if post.goalie_name:
        if post.goalie_n_bucket:
            lines.append(
                f"- Goalie: **{post.goalie_name}** — {post.goalie_n_bucket} shots in this exact bucket "
                f"({post.goalie_n_total:,} total)."
            )
        else:
            lines.append(
                f"- Goalie: **{post.goalie_name}** — 0 shots in this exact bucket; posterior reverts to league."
            )
    lines.append(f"- Method: {post.method}")
    lines.append("")
    lines.append("| Outcome | Posterior mean | 90% CI | League mean |")
    lines.append("|---|---|---|---|")
    for r in post.rows:
        lines.append(
            f"| {r.label} | **{r.mean:.1%}** | {r.lo:.1%} – {r.hi:.1%} | {r.league_mean:.1%} |"
        )
    return "\n".join(lines)
