# GoalieAI — 3D Scene Viewer

Lightweight three.js viewer that renders a hockey scenario from **scene data**
(player + puck positions in rink coordinates) instead of NHL footage. The same
scene can be viewed broadcast-style, from behind the net, the goalie's eyes, or
overhead, and players can be dragged to author new looks. All geometry is
original — no copyrighted images.

## Run it

The viewer is served by the local app — start `app/server.py` and open
**http://127.0.0.1:8000/viewer/**. No separate server needed.

Standalone (three.js loads from a CDN via import map, scenes are fetched as
JSON, so you need a web server, not `file://`):

```bash
cd viewer
python3 -m http.server 8000
# open http://localhost:8000
```

## Controls

| Control | What it does |
|---------|--------------|
| Drag / scroll | Orbit and zoom the camera |
| Camera buttons | Jump to Broadcast / Behind Net / Goalie POV / Overhead |
| Scenario dropdown | Switch between scenes in `scenes/` |
| Overlays | Toggle royal road, shot line, pass lanes |
| **Move players: ON** | Drag any skater/puck on the ice; coordinates update live |
| Reset scene | Reload the original positions |

## Coordinate system

Matches MoneyPuck shot data, in feet:

- `x` north-south, attacking net at **x = 89**, blue line at x = 25, center x = 0
- `y` east-west, center ice **y = 0**, boards at y = ±42.5

## Scene format

One scenario = one JSON file in `scenes/`:

```json
{
  "id": "2026-05-26-2on1-delay",
  "title": "2-on-1 — Carrier vs. Cross-Crease",
  "situation_family": "odd_man_rush",
  "manpower": "5v5",
  "default_camera": "broadcast",
  "puck": { "x": 69, "y": -20 },
  "entities": [
    { "id": "carrier", "team": "offense", "role": "carrier",
      "x": 69, "y": -20, "facing": 45, "stick": "left" },
    { "id": "goalie", "team": "goalie", "role": "goalie", "x": 86, "y": -3 }
  ],
  "overlays": { "royal_road": true, "pass_lanes": [["carrier", "trailer"]] }
}
```

- `team`: `offense` (dark) | `defense` (light) | `goalie` (gold)
- `facing`: degrees, `0` points toward the attacking net (+x)
- `stick`: `left` | `right`
- To add a scene to the dropdown, drop the file in `scenes/` and add its name to
  `SCENES` in `src/main.js`.

## Exporting a still

The viewer renders the stills the local app serves from `content/stills/`. Two ways
to capture one:

- **Export button** — frame the scene and click **Export still (PNG)**. The file
  downloads as `<scene id>.png`; move it into `content/stills/`.
- **Capture URL** — deep-link straight to a clean, UI-free frame using query params:

```
http://127.0.0.1:8000/viewer/?scene=slot_seam&camera=broadcast&hideui=1
```

  - `scene` — a scene name from `scenes/` (must be listed in `SCENES` in `src/main.js`)
  - `camera` — `broadcast` | `behind_net` | `goalie_pov` | `overhead`
  - `hideui=1` — hides the control panel/readout so the whole frame is just the ice

The filename must match the `image_path` in `content/still_image_of_the_day.json`
(e.g. `content/stills/2026-05-28-slot-seam-pass.png`).

## Seeding a scene from a shot

`scripts/shot_to_scene.py` turns a shot location into a starting scene (puck at
the shot, goalie on the angle, template skaters to drag):

```bash
# From explicit coordinates (no data download needed)
python3 ../scripts/shot_to_scene.py --x 72 --y -16 --family east_west_seam \
    --hand R --out scenes/my_seam.json

# From a MoneyPuck shot-level CSV (download Shot Data from moneypuck.com/data.htm)
python3 ../scripts/shot_to_scene.py --csv ../data/moneypuck/raw/shots_2024.csv --row 0 \
    --out scenes/mp_shot.json
```

> The local `goalies_2008_to_2024.csv` has no x/y coordinates. To seed scenes
> from real shots, download a **shot-level** CSV (has `xCordAdjusted` /
> `yCordAdjusted`) from MoneyPuck's data page. Credit MoneyPuck.com.
```
