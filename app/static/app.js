const $ = (id) => document.getElementById(id);

const state = {
  current: null,    // { slug, scene, posterior, features }
  heatmap: null,    // { hex: {h{x}_{y}: {xg, n}}, grid: {...} }
};

async function loadHeatmap() {
  try {
    const r = await fetch("/api/heatmap").then((r) => r.json());
    state.heatmap = r;
  } catch {
    state.heatmap = null;
  }
}

function sceneViewerUrl(slug) {
  return `/viewer/?scene=${encodeURIComponent(slug)}&embed=1`;
}

async function loadRandomShot() {
  $("intro").innerHTML = '<span class="intro-loading">Reading the scene…</span>';
  $("analysis").innerHTML = '<span class="intro-loading">Building the full breakdown…</span>';
  $("bayes-summary").innerHTML = '<span class="intro-loading">Sampling shot from MoneyPuck 2018–2024…</span>';
  $("bayes-bars").innerHTML = "";
  $("bayes-rink").innerHTML = "";
  $("bayes-method-text").textContent = "";
  try {
    const res = await fetch("/api/random-shot");
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    const r = await res.json();
    state.current = r;
    $("scene-frame").src = sceneViewerUrl(r.slug);
    $("scene-frame").hidden = false;
    $("empty").hidden = true;
    const src = r.scene.source || {};
    $("counter").textContent =
      `${src.shooter || "shot"} · ${(r.scene.situation_family || "").replaceAll("_", " ")} · ${r.scene.manpower}` +
      (src.season ? ` · ${src.season}` : "");
    renderBayes(r);
    loadIntro(r.slug);
    loadAnalysis(r.slug);
  } catch (err) {
    console.error("random-shot failed", err);
    $("bayes-summary").innerHTML =
      `<b>Sampler error.</b> Open DevTools → Network → <code>/api/random-shot</code> ` +
      `to see the response body, or check the server console.<br>` +
      `<code>${(err && err.message) || err}</code>`;
  }
}

function renderBayes(payload) {
  const post = payload.posterior;
  const src = payload.scene.source || {};
  const feats = payload.features || {};
  const pct = (v) => `${(v * 100).toFixed(1)}%`;
  const zoneLabel = (post.zone || "—").replaceAll("_", " ");
  const goalieLine = post.goalie_name
    ? `<b>${post.goalie_name}</b>` +
      (post.goalie_n_bucket
        ? ` — <b>${post.goalie_n_bucket}</b> shots in this exact bucket ` +
          `(out of ${post.goalie_n_total.toLocaleString()} total)`
        : ` — no shots in this exact bucket; falling back to league`)
    : "no goalie identified";
  const xgLine = post.league_xg_mean != null
    ? `· league xG mean ${post.league_xg_mean.toFixed(3)}`
    : "";
  const obsLine = src.observed_outcome
    ? `<div class="bayes-observed">Actual outcome on this shot: <b>${src.observed_outcome.replaceAll("_", " ")}</b>${src.x_goal ? ` · MoneyPuck xG ${src.x_goal.toFixed(3)}` : ""}</div>`
    : "";

  $("bayes-summary").innerHTML = `
    <div><b>${zoneLabel}</b> · ${post.manpower} · hex <code>${post.hex_cell || "—"}</code>
      · league bucket N = <b>${post.league_n.toLocaleString()}</b> ${xgLine}</div>
    <div>${goalieLine}</div>
    ${obsLine}`;
  $("bayes-method-text").textContent = post.method;
  $("bayes-bars").innerHTML = renderPosteriorBars(post.rows);
  $("bayes-rink").innerHTML = renderRink(payload);
}

function renderPosteriorBars(rows) {
  const maxHi = Math.max(...rows.map((r) => r.hi), 0.5);
  const W = 360;
  const labelW = 130;
  const barW = W - labelW - 70;
  const rowH = 30;
  const H = rows.length * rowH + 28;
  const x = (v) => labelW + (v / maxHi) * barW;
  const ticks = [];
  for (let t = 0; t <= maxHi; t += maxHi > 0.4 ? 0.1 : 0.05) ticks.push(t);
  let svg = `<svg viewBox="0 0 ${W} ${H}" class="bayes-svg">`;
  // axis
  ticks.forEach((t) => {
    const xi = x(t);
    svg += `<line x1="${xi}" x2="${xi}" y1="14" y2="${H - 12}" stroke="#1f2a36" stroke-width="1"/>`;
    svg += `<text x="${xi}" y="10" font-size="9" fill="#6c7d8c" text-anchor="middle">${Math.round(t * 100)}%</text>`;
  });
  rows.forEach((r, i) => {
    const y = 22 + i * rowH;
    const cy = y + 8;
    svg += `<text x="${labelW - 6}" y="${cy + 4}" font-size="11" fill="#cdd6e0" text-anchor="end">${r.label}</text>`;
    // league baseline (faint tick)
    svg += `<line x1="${x(r.league_mean)}" x2="${x(r.league_mean)}" y1="${cy - 9}" y2="${cy + 9}" stroke="#8aa0b3" stroke-width="1" stroke-dasharray="2 2"/>`;
    // CI bar
    svg += `<rect x="${x(r.lo)}" y="${cy - 6}" width="${Math.max(1, x(r.hi) - x(r.lo))}" height="12" rx="3" fill="#4a90d9" opacity="0.35"/>`;
    // posterior mean
    svg += `<circle cx="${x(r.mean)}" cy="${cy}" r="4" fill="#4a90d9"/>`;
    // pct label
    svg += `<text x="${x(r.hi) + 6}" y="${cy + 4}" font-size="10" fill="#e8edf2">${(r.mean * 100).toFixed(1)}%</text>`;
  });
  svg += `<text x="${labelW}" y="${H - 2}" font-size="9" fill="#6c7d8c">● posterior mean · bar = 90% CI · dashed = league mean</text>`;
  svg += `</svg>`;
  return svg;
}

function renderRink(payload) {
  if (!state.heatmap) return "";
  const grid = state.heatmap.grid;
  const hex = state.heatmap.hex;
  // Show the offensive zone (x: blue-line=25 → end boards=100, y: -42→43).
  const W = 360, H = 200;
  const xmin = 25, xmax = 100;
  const ymin = grid.y_min, ymax = grid.y_max;
  const sx = (rinkX) => ((rinkX - xmin) / (xmax - xmin)) * W;
  const sy = (rinkY) => H - ((rinkY - ymin) / (ymax - ymin)) * H;
  const cell = grid.cell_size;
  const px = ((cell) / (xmax - xmin)) * W;
  const py = ((cell) / (ymax - ymin)) * H;

  // Find max xg for color scale
  let maxXg = 0;
  for (const k in hex) maxXg = Math.max(maxXg, hex[k].xg);

  let svg = `<svg viewBox="0 0 ${W} ${H}" class="bayes-svg">`;
  // Background
  svg += `<rect x="0" y="0" width="${W}" height="${H}" fill="#0d1620"/>`;
  // Hex/grid cells
  for (const k in hex) {
    const m = /^h(\d+)_(\d+)$/.exec(k);
    if (!m) continue;
    const cxIdx = +m[1], cyIdx = +m[2];
    const rinkX = xmin + cxIdx * cell;
    const rinkY = ymin + cyIdx * cell;
    if (rinkX < xmin || rinkX > xmax) continue;
    const intensity = Math.min(1, hex[k].xg / Math.max(maxXg, 0.01));
    const a = 0.05 + intensity * 0.75;
    svg += `<rect x="${sx(rinkX)}" y="${sy(rinkY + cell)}" width="${px}" height="${py}" fill="rgba(255,86,86,${a.toFixed(3)})"/>`;
  }
  // Goal line + crease
  svg += `<line x1="${sx(89)}" x2="${sx(89)}" y1="0" y2="${H}" stroke="#5a6c80" stroke-width="1"/>`;
  svg += `<line x1="${sx(25)}" x2="${sx(25)}" y1="0" y2="${H}" stroke="#4a90d9" stroke-width="1"/>`;
  // Faceoff dots (approx)
  [[69, 22], [69, -22]].forEach(([x, y]) => {
    svg += `<circle cx="${sx(x)}" cy="${sy(y)}" r="2.5" fill="#5a6c80"/>`;
  });
  // Shot location
  const puck = payload.scene.puck;
  if (puck) {
    svg += `<circle cx="${sx(puck.x)}" cy="${sy(puck.y)}" r="6" fill="#fff" stroke="#000" stroke-width="1"/>`;
    svg += `<text x="${sx(puck.x) + 9}" y="${sy(puck.y) + 4}" font-size="10" fill="#fff">shot</text>`;
  }
  // Goalie
  const goalie = (payload.scene.entities || []).find((e) => e.role === "goalie");
  if (goalie) {
    svg += `<circle cx="${sx(goalie.x)}" cy="${sy(goalie.y)}" r="4" fill="#ffd166"/>`;
  }
  svg += `<text x="4" y="12" font-size="10" fill="#8aa0b3">League xG heatmap · offensive zone</text>`;
  svg += `</svg>`;
  return svg;
}

async function loadIntro(slug) {
  try {
    const r = await fetch("/api/intro", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: slug }),
    }).then((r) => r.json());
    if (!state.current || state.current.slug !== slug) return;
    $("intro").innerHTML = renderMarkdown(r.markdown || "");
  } catch {
    $("intro").innerHTML = '<span class="intro-loading">Coach intro unavailable.</span>';
  }
}

async function loadAnalysis(slug) {
  try {
    const r = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: slug }),
    }).then((r) => r.json());
    if (!state.current || state.current.slug !== slug) return;
    $("analysis").innerHTML = renderMarkdown(r.markdown || "");
  } catch {
    $("analysis").innerHTML = '<span class="intro-loading">Analysis failed — hit Refresh.</span>';
  }
}

// Minimal markdown → HTML (headings, bold, italic, lists, tables, code).
function renderMarkdown(md) {
  const escape = (s) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const lines = md.split("\n");
  let html = "";
  let inList = null;
  let inTable = false;
  const flushList = () => {
    if (inList) {
      html += `</${inList}>`;
      inList = null;
    }
  };
  const flushTable = () => {
    if (inTable) {
      html += "</tbody></table>";
      inTable = false;
    }
  };
  const inline = (s) =>
    escape(s)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      flushList(); flushTable();
      const level = h[1].length;
      html += `<h${level}>${inline(h[2])}</h${level}>`;
      continue;
    }
    const ul = line.match(/^[-*]\s+(.*)$/);
    if (ul) {
      flushTable();
      if (inList !== "ul") { flushList(); html += "<ul>"; inList = "ul"; }
      html += `<li>${inline(ul[1])}</li>`;
      continue;
    }
    const ol = line.match(/^\d+\.\s+(.*)$/);
    if (ol) {
      flushTable();
      if (inList !== "ol") { flushList(); html += "<ol>"; inList = "ol"; }
      html += `<li>${inline(ol[1])}</li>`;
      continue;
    }
    if (/^\|.+\|$/.test(line)) {
      flushList();
      const cells = line.split("|").slice(1, -1).map((c) => c.trim());
      if (!inTable) {
        if (lines[i + 1] && /^\|[-:\s|]+\|$/.test(lines[i + 1])) {
          html += "<table><thead><tr>" +
            cells.map((c) => `<th>${inline(c)}</th>`).join("") +
            "</tr></thead><tbody>";
          inTable = true; i++;
          continue;
        }
      } else {
        html += "<tr>" + cells.map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>";
        continue;
      }
    }
    if (line.trim() === "") { flushList(); flushTable(); continue; }
    flushList(); flushTable();
    html += `<p>${inline(line)}</p>`;
  }
  flushList(); flushTable();
  return html;
}

$("next-btn").addEventListener("click", loadRandomShot);

(async () => {
  await loadHeatmap();
  await loadRandomShot();
})();
