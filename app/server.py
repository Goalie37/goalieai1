"""GoalieAI local app — interactive scenario teach-back + coach reveal.

Uses the Claude Agent SDK, which reuses your local Claude Code login —
no separate ANTHROPIC_API_KEY required.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Literal

from claude_agent_sdk import ClaudeAgentOptions, query
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import bayes
from app.shotscene import bayes_features, scene_from_row

ROOT = Path(__file__).resolve().parent.parent
SCENES_DIR = ROOT / "viewer" / "scenes"
STATIC_DIR = Path(__file__).resolve().parent / "static"
VIEWER_DIR = ROOT / "viewer"
METADATA_PATH = ROOT / "content" / "still_image_of_the_day.json"
SHOTS_INDEX_PATH = ROOT / "data" / "derived" / "shots_index.parquet"

KNOWLEDGE_FILES = [
    ROOT / "knowledge" / "goalie_master_playbook.md",
    ROOT / "knowledge" / "situation_relationship_graph.md",
    ROOT / "knowledge" / "assumption_framework.md",
    ROOT / "knowledge" / "bayesian_reasoning.md",
    ROOT / "knowledge" / "moneypuck_priors.json",
]
TEACH_BACK_PROMPT = ROOT / "prompts" / "goalie_teach_back_mode.md"
SCENARIO_PROMPT = ROOT / "prompts" / "goalie_scenario_agent.md"

MODEL = os.environ.get("GOALIEAI_MODEL")  # None → SDK default

app = FastAPI(title="GoalieAI")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _metadata_by_id() -> dict[str, dict]:
    if not METADATA_PATH.exists():
        return {}
    try:
        data = json.loads(_read(METADATA_PATH))
    except json.JSONDecodeError:
        return {}
    return {s["id"]: s for s in data.get("scenarios", []) if "id" in s}


def _scenario_path(slug: str) -> Path:
    p = (SCENES_DIR / f"{slug}.json").resolve()
    if not str(p).startswith(str(SCENES_DIR.resolve())) or not p.exists():
        raise HTTPException(404, "Scenario not found")
    return p


def _load_scene(slug: str) -> dict:
    """Return scene JSON from cache (synthetic) or disk (curated)."""
    with SCENE_CACHE_LOCK:
        entry = SCENE_CACHE.get(slug)
    if entry is not None:
        return entry["scene"]
    return json.loads(_read(_scenario_path(slug)))


def _list_scenarios() -> list[dict]:
    if not SCENES_DIR.is_dir():
        return []
    meta = _metadata_by_id()
    out: list[dict] = []
    for path in sorted(SCENES_DIR.glob("*.json")):
        try:
            scene = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        sid = scene.get("id", path.stem)
        extra = meta.get(sid, {})
        out.append(
            {
                "slug": path.stem,
                "id": sid,
                "title": scene.get("title", path.stem),
                "situation_family": scene.get("situation_family"),
                "manpower": scene.get("manpower"),
                "level": extra.get("level"),
                "tags": extra.get("tags"),
                "situation_hint": extra.get("situation_hint"),
            }
        )
    return out


def _scenario_context(slug: str) -> str:
    scene = _load_scene(slug)
    sid = scene.get("id", slug)
    meta = _metadata_by_id().get(sid, {})
    parts = [
        f"Scenario slug: {slug}",
        f"Scenario id: {sid}",
        "",
        "=== SCENE DATA (JSON) ===",
        json.dumps(scene, indent=2),
    ]
    if meta:
        parts.extend(
            [
                "",
                "=== SUPPLEMENTAL METADATA (not visible in 3D view) ===",
                json.dumps(
                    {
                        k: meta[k]
                        for k in (
                            "title",
                            "level",
                            "tags",
                            "situation_hint",
                            "manpower",
                        )
                        if k in meta
                    },
                    indent=2,
                ),
            ]
        )
    return "\n".join(parts)


def _knowledge_bundle() -> str:
    parts = [f"=== {f.name} ===\n{_read(f)}" for f in KNOWLEDGE_FILES]
    return "\n\n".join(parts)


def _teachback_to_text(tb: "TeachBack") -> str:
    return (
        f"### 1. Situation type\n{tb.situation_type}\n\n"
        f"### 2. Must happen\n{tb.must_happen}\n\n"
        f"### 3. Could happen\n{tb.could_happen}\n\n"
        f"### 4. Doesn't need to happen\n{tb.doesnt_need}\n\n"
        f"### 5. Key relationship\n{tb.relationship_from} → {tb.relationship_to}\n\n"
        f"### 6. Primary read\n{tb.primary_read}\n\n"
        f"### 7. Biggest threat in 2 seconds\n{tb.biggest_threat}\n"
    )


class TeachBack(BaseModel):
    scenario: str  # viewer/scenes/<slug>.json stem
    situation_type: str
    must_happen: str
    could_happen: str
    doesnt_need: str
    relationship_from: str
    relationship_to: str
    primary_read: str
    biggest_threat: str


class AgentResponse(BaseModel):
    markdown: str
    mode: Literal["intro", "review", "reveal", "analysis"]


class IntroRequest(BaseModel):
    scenario: str


class AnalyzeRequest(BaseModel):
    scenario: str


async def _run(system_prompt: str, user_prompt: str) -> str:
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=["Read"],
        cwd=str(ROOT),
        permission_mode="acceptEdits",
        **({"model": MODEL} if MODEL else {}),
    )
    chunks: list[str] = []
    async for msg in query(prompt=user_prompt, options=options):
        content = getattr(msg, "content", None)
        if not content:
            continue
        for block in content:
            text = getattr(block, "text", None)
            if text:
                chunks.append(text)
    return "".join(chunks).strip()


def _system(mode_prompt: Path, role_instructions: str) -> str:
    return (
        _read(mode_prompt)
        + "\n\n=== KNOWLEDGE BUNDLE ===\n"
        + _knowledge_bundle()
        + "\n\n=== RUNTIME INSTRUCTIONS ===\n"
        + role_instructions
    )


# ---- Random MoneyPuck shot mode ----------------------------------------

import threading
from collections import OrderedDict

SCENE_CACHE: "OrderedDict[str, dict]" = OrderedDict()
SCENE_CACHE_MAX = 200
SCENE_CACHE_LOCK = threading.Lock()
_SHOTS_DF = None


def _shots_df():
    global _SHOTS_DF
    if _SHOTS_DF is None:
        import pandas as pd  # local import — heavy
        if not SHOTS_INDEX_PATH.exists():
            raise RuntimeError(
                f"Missing {SHOTS_INDEX_PATH}. Run `python3 scripts/build_priors.py` first."
            )
        _SHOTS_DF = pd.read_parquet(SHOTS_INDEX_PATH)
    return _SHOTS_DF


def _remember_scene(slug: str, scene: dict, posterior_payload: dict) -> None:
    with SCENE_CACHE_LOCK:
        SCENE_CACHE[slug] = {"scene": scene, "posterior": posterior_payload}
        SCENE_CACHE.move_to_end(slug)
        while len(SCENE_CACHE) > SCENE_CACHE_MAX:
            SCENE_CACHE.popitem(last=False)


@app.get("/api/scenarios")
def list_scenarios() -> dict:
    """Compatibility shim — returns cached random shots (most recent first)."""
    with SCENE_CACHE_LOCK:
        items = []
        for slug, entry in reversed(SCENE_CACHE.items()):
            sc = entry["scene"]
            items.append({
                "slug": slug,
                "id": sc.get("id", slug),
                "title": sc.get("title", slug),
                "situation_family": sc.get("situation_family"),
                "manpower": sc.get("manpower"),
            })
    return {"scenarios": items}


@app.get("/api/random-shot")
def random_shot() -> dict:
    """Sample one MoneyPuck shot and return slug + scene + Bayesian posterior."""
    df = _shots_df()
    row = df.sample(n=1).iloc[0].to_dict()
    scene = scene_from_row(row)
    feats = bayes_features(row)
    post = bayes.posterior(
        zone=feats["zone"],
        manpower=feats["manpower"],
        hex_cell=feats["hex_cell"],
        goalie_id=feats["goalie_id"],
    )
    payload = {
        "slug": scene["id"],
        "scene": scene,
        "posterior": post.to_dict(),
        "features": feats,
    }
    _remember_scene(scene["id"], scene, payload["posterior"])
    return payload


@app.get("/api/heatmap")
def heatmap() -> dict:
    return {"hex": bayes.hex_xg_map(), "grid": bayes.hex_grid_meta()}


@app.get("/viewer/scenes/{slug}.json")
def viewer_scene(slug: str):
    """Serve cached synthetic scenes. Falls through to static file for curated slugs."""
    with SCENE_CACHE_LOCK:
        entry = SCENE_CACHE.get(slug)
    if entry is not None:
        return JSONResponse(entry["scene"])
    # Fall back to the on-disk curated scene if present
    p = SCENES_DIR / f"{slug}.json"
    if p.exists():
        return JSONResponse(json.loads(_read(p)))
    raise HTTPException(404, "Scene not found")


@app.post("/api/intro", response_model=AgentResponse)
async def intro(req: IntroRequest) -> AgentResponse:
    """Coach speaks first — short, no-spoiler framing of THIS scenario."""
    _load_scene(req.scenario)  # 404 if missing
    system = _system(
        TEACH_BACK_PROMPT,
        "You are in `prompt_teaching` mode. The user is about to study the "
        "3D scenario below and write a teach-back. Speak as the coach in "
        "2–4 short sentences:\n"
        "  1. Name the situation family you see (rush, seam, cycle, point shot, etc.)\n"
        "  2. Point to 1–2 cues worth scanning — without naming the primary read.\n"
        "  3. Invite them to teach the frame.\n"
        "Hard rules: NO primary read, NO outcome paths, NO Bayesian content, "
        "NO scoring. Plain prose only — no headings, no lists, no JSON. "
        "Use playbook vocabulary.",
    )
    user = (
        f"{_scenario_context(req.scenario)}\n\n"
        "Write your short coach intro for this scenario."
    )
    return AgentResponse(markdown=await _run(system, user), mode="intro")


@app.post("/api/analyze", response_model=AgentResponse)
async def analyze(req: AnalyzeRequest) -> AgentResponse:
    """Full coach analysis of the scene — no teach-back required."""
    scene = _load_scene(req.scenario)
    # Recover Bayesian evidence for this scene if it came from MoneyPuck.
    bayes_block = ""
    with SCENE_CACHE_LOCK:
        entry = SCENE_CACHE.get(req.scenario)
    if entry is not None and entry.get("posterior"):
        post_dict = entry["posterior"]
        # Reconstruct Posterior just for the markdown helper
        rows = [bayes.PosteriorRow(**r) for r in post_dict["rows"]]
        post = bayes.Posterior(
            zone=post_dict["zone"], manpower=post_dict["manpower"],
            hex_cell=post_dict["hex_cell"], league_n=post_dict["league_n"],
            league_xg_mean=post_dict["league_xg_mean"],
            goalie_id=post_dict["goalie_id"], goalie_name=post_dict["goalie_name"],
            goalie_n_bucket=post_dict["goalie_n_bucket"],
            goalie_n_total=post_dict["goalie_n_total"],
            rows=rows, method=post_dict["method"],
        )
        bayes_block = "\n\n=== BAYESIAN EVIDENCE ===\n" + bayes.evidence_markdown(post)
    system = _system(
        SCENARIO_PROMPT,
        "You are delivering a full coach analysis directly — no teach-back was "
        "submitted, so skip the Teach-Back Delta. The scenario is provided as "
        "JSON (3D scene data — player/puck positions, roles, overlays). "
        "A Bayesian evidence block (computed from MoneyPuck 2018–2024 shot data "
        "for this exact zone × manpower bucket, with goalie-specific update when "
        "available) is also attached. You MUST cite at least two specific numbers "
        "from that table in your Bayesian branches and Primary Read sections — "
        "name the posterior mean and the 90% credible interval, and explain how "
        "they shift the read. Execute the full Analysis Protocol: visual cues, "
        "situation classification, scan checklist, assumptions, relationship map, "
        "Bayesian branches (grounded in the attached evidence), primary read, 3–5 "
        "outcome paths, handedness/screens, confidence. Output Markdown only — "
        "skip the JSON code block.",
    )
    user = (
        f"Scenario id: {scene.get('id', req.scenario)}\n"
        f"Generated at: {dt.datetime.utcnow().isoformat()}Z\n\n"
        f"{_scenario_context(req.scenario)}"
        f"{bayes_block}\n\n"
        "Deliver the full coach analysis."
    )
    return AgentResponse(markdown=await _run(system, user), mode="analysis")


@app.post("/api/review", response_model=AgentResponse)
async def review(tb: TeachBack) -> AgentResponse:
    _scenario_path(tb.scenario)
    system = _system(
        TEACH_BACK_PROMPT,
        "You are in `review_teaching` mode. The user studied an interactive 3D "
        "hockey scenario and submitted the teach-back below. The scenario is "
        "provided as JSON (player/puck coordinates, roles, situation family). "
        "You may use the Read tool on the scene file path if you need to "
        "re-open it. Follow the teach-back review protocol and output the "
        "Markdown review section only — no JSON. "
        "End with `NEXT_STEP: retry_teach_back` or `NEXT_STEP: coach_reveal`.",
    )
    user = (
        f"{_scenario_context(tb.scenario)}\n\n"
        f"User teach-back submission:\n\n{_teachback_to_text(tb)}"
    )
    return AgentResponse(markdown=await _run(system, user), mode="review")


@app.post("/api/reveal", response_model=AgentResponse)
async def reveal(tb: TeachBack) -> AgentResponse:
    path = _scenario_path(tb.scenario)
    scene = json.loads(_read(path))
    system = _system(
        SCENARIO_PROMPT,
        "You are in `coach_reveal` mode. The user already submitted the teach-back "
        "below. The scenario is provided as JSON (3D scene data — positions, "
        "roles, overlays). You may use the Read tool on the scene file path. "
        "Execute the full Analysis Protocol and append the Teach-Back Delta "
        "section. Output Markdown only — skip the JSON code block.",
    )
    user = (
        f"Scenario id: {scene.get('id', tb.scenario)}\n"
        f"Generated at: {dt.datetime.utcnow().isoformat()}Z\n\n"
        f"{_scenario_context(tb.scenario)}\n\n"
        f"User teach-back:\n\n{_teachback_to_text(tb)}"
    )
    return AgentResponse(markdown=await _run(system, user), mode="reveal")


app.mount("/viewer", StaticFiles(directory=str(VIEWER_DIR), html=True), name="viewer")
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
