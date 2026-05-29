import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { DragControls } from "three/addons/controls/DragControls.js";

import { buildRink, rinkToWorld, RINK } from "./rink.js";
import { buildPlayer, buildPuck } from "./entities.js";
import { cameraPose, PRESETS, PRESET_LABELS } from "./cameras.js";

// Fallback if /api/scenarios is unavailable (standalone viewer server).
const SCENES_FALLBACK = [
  "2on1_delay",
  "wrap_low",
  "slot_seam",
  "point_screen",
];
let SCENES = [...SCENES_FALLBACK];

const state = {
  sceneData: null,
  draggables: [],
  overlayGroup: null,
  dragEnabled: false,
  cameraPreset: "broadcast",
  goaliePov: null,
};

const GOALIE_YAW_LIMIT = THREE.MathUtils.degToRad(55);
const GOALIE_WHEEL_SENS = 0.0018;
const GOALIE_DRAG_SENS = 0.004;

const canvas = document.getElementById("view");
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  preserveDrawingBuffer: true, // required so the canvas can be captured to PNG
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b1016);

const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 2000);
camera.position.set(40, 55, 78);

const orbit = new OrbitControls(camera, canvas);
orbit.enableDamping = true;
orbit.target.set(74, 0, 0);

// Lights
scene.add(new THREE.HemisphereLight(0xffffff, 0x223344, 0.9));
const key = new THREE.DirectionalLight(0xffffff, 1.1);
key.position.set(30, 120, 60);
key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
key.shadow.camera.left = -120;
key.shadow.camera.right = 120;
key.shadow.camera.top = 120;
key.shadow.camera.bottom = -120;
scene.add(key);

const rink = buildRink();
scene.add(rink);

let dragControls = null;

function clearGroupByName(name) {
  const existing = scene.getObjectByName(name);
  if (existing) scene.remove(existing);
}

function loadScene(sceneData) {
  state.sceneData = sceneData;

  // Remove previous entities + overlays.
  state.draggables.forEach((d) => scene.remove(d));
  state.draggables = [];
  clearGroupByName("overlays");

  const puck = buildPuck(sceneData.puck);
  scene.add(puck);
  state.draggables.push(puck);

  sceneData.entities.forEach((e) => {
    const mesh = buildPlayer(e);
    scene.add(mesh);
    state.draggables.push(mesh);
  });

  rebuildOverlays();
  setCamera(sceneData.default_camera ?? "broadcast");
  setupDragControls();
  refreshReadout();
  document.getElementById("scene-title").textContent = sceneData.title;
  document.getElementById("scene-meta").textContent =
    `${sceneData.situation_family} · ${sceneData.manpower ?? "5v5"}`;
}

function worldOf(id) {
  const obj = state.draggables.find((d) => d.name === id);
  return obj ? obj.position.clone() : null;
}

/** Back of the net, center of the mouth (matches rink.js netting plane). */
function netBackCenter(goalX = RINK.goalLine) {
  return rinkToWorld(goalX + RINK.netDepth, 0, RINK.netHeight / 2);
}

/** Shot line: puck on the ice → back of the net, center of the mouth. */
function shotLineEndpoints() {
  const puckMesh = state.draggables.find((d) => d.name === "puck");
  const puckData = state.sceneData?.puck;
  const ud = puckMesh?.userData;
  const rinkX = ud?.x ?? puckData?.x;
  const rinkY = ud?.y ?? puckData?.y;
  if (rinkX == null || rinkY == null) return null;
  const origin = rinkToWorld(rinkX, rinkY, 0.25);
  const goal = netBackCenter();
  return { origin, goal };
}

function dashedLine(a, b, color, y = 0.3) {
  const geo = new THREE.BufferGeometry().setFromPoints([
    a.clone().setY(y),
    b.clone().setY(y),
  ]);
  const mat = new THREE.LineDashedMaterial({
    color,
    dashSize: 2,
    gapSize: 1.4,
  });
  const line = new THREE.Line(geo, mat);
  line.computeLineDistances();
  return line;
}

/** Dashed segment using true 3D endpoints (e.g. puck on ice → back of net). */
function dashedLine3D(a, b, color, { onTop = false, linewidth = 1 } = {}) {
  const geo = new THREE.BufferGeometry().setFromPoints([a.clone(), b.clone()]);
  const mat = new THREE.LineDashedMaterial({
    color,
    dashSize: 2,
    gapSize: 1.4,
    linewidth,
    depthTest: !onTop,
    transparent: onTop,
  });
  const line = new THREE.Line(geo, mat);
  line.computeLineDistances();
  if (onTop) line.renderOrder = 999;
  return line;
}

function rebuildOverlays() {
  clearGroupByName("overlays");
  const group = new THREE.Group();
  group.name = "overlays";
  const ov = state.sceneData.overlays ?? {};

  if (ov.royal_road && document.getElementById("ov-royal")?.checked !== false) {
    group.add(
      dashedLine(
        rinkToWorld(RINK.goalLine, 0, 0),
        rinkToWorld(RINK.blueLine, 0, 0),
        0xf1c40f,
      ),
    );
  }

  if (document.getElementById("ov-shot")?.checked !== false) {
    const shot = shotLineEndpoints();
    if (shot) {
      // Always-on-top so the trajectory visibly cuts through the crease,
      // the goalie, and the netting all the way to the back of the net.
      group.add(dashedLine3D(shot.origin, shot.goal, 0xe74c3c, { onTop: true }));
    }
  }

  if (
    Array.isArray(ov.pass_lanes) &&
    document.getElementById("ov-lanes")?.checked !== false
  ) {
    ov.pass_lanes.forEach(([from, to]) => {
      const a = worldOf(from);
      const b = worldOf(to);
      if (a && b) group.add(dashedLine(a, b, 0x2ecc71));
    });
  }

  state.overlayGroup = group;
  scene.add(group);
}

function setupDragControls() {
  if (dragControls) dragControls.dispose();
  dragControls = new DragControls(state.draggables, camera, canvas);
  dragControls.enabled = state.dragEnabled;

  dragControls.addEventListener("dragstart", () => (orbit.enabled = false));
  dragControls.addEventListener("dragend", () => {
    orbit.enabled = state.cameraPreset !== "goalie_pov";
    refreshReadout();
  });
  dragControls.addEventListener("drag", (e) => {
    // Constrain to the ice plane and update rink coordinates.
    e.object.position.y = 0;
    const ud = e.object.userData;
    ud.x = +e.object.position.x.toFixed(1);
    ud.y = +(-e.object.position.z).toFixed(1);
    rebuildOverlays();
  });
}

function resetOrbitLimits() {
  orbit.enableZoom = true;
  orbit.enablePan = true;
  orbit.enableRotate = true;
  orbit.minDistance = 0;
  orbit.maxDistance = Infinity;
  orbit.minPolarAngle = 0;
  orbit.maxPolarAngle = Math.PI;
}

function setGoalieMeshVisible(visible) {
  const goalie = state.draggables.find((d) => d.name === "goalie");
  if (goalie) goalie.visible = visible;
}

function applyGoaliePovLook() {
  const gp = state.goaliePov;
  if (!gp) return;
  const dir = gp.centerDir
    .clone()
    .applyAxisAngle(new THREE.Vector3(0, 1, 0), gp.yaw);
  camera.position.copy(gp.eye);
  camera.lookAt(gp.eye.clone().add(dir.multiplyScalar(80)));
}

function setCamera(preset) {
  state.cameraPreset = preset;
  const pose = cameraPose(preset, state.sceneData);
  camera.fov = pose.fov ?? 50;
  camera.updateProjectionMatrix();

  if (preset === "goalie_pov") {
    const centerDir =
      pose.forward ??
      new THREE.Vector3().subVectors(pose.target, pose.position).normalize();
    state.goaliePov = {
      eye: pose.position.clone(),
      centerDir,
      yaw: 0,
    };
    orbit.enabled = false;
    setGoalieMeshVisible(false);
    applyGoaliePovLook();
    setControlHint("scroll to look left / right · drag to turn head");
  } else {
    state.goaliePov = null;
    setGoalieMeshVisible(true);
    orbit.enabled = true;
    resetOrbitLimits();
    camera.position.copy(pose.position);
    orbit.target.copy(pose.target);
    orbit.update();
    setControlHint("drag to orbit · scroll to zoom");
  }

  document.querySelectorAll("[data-cam]").forEach((b) => {
    b.classList.toggle("active", b.dataset.cam === preset);
  });
}

function setControlHint(text) {
  const hint = document.getElementById("hint");
  const embedHint = document.querySelector("#embed-bar .embed-hint");
  if (hint) hint.textContent = text;
  if (embedHint) embedHint.textContent = text;
}

function clampGoalieYaw() {
  const gp = state.goaliePov;
  if (!gp) return;
  gp.yaw = THREE.MathUtils.clamp(gp.yaw, -GOALIE_YAW_LIMIT, GOALIE_YAW_LIMIT);
}

function onGoalieWheel(e) {
  if (state.cameraPreset !== "goalie_pov" || !state.goaliePov) return;
  e.preventDefault();
  state.goaliePov.yaw -= e.deltaY * GOALIE_WHEEL_SENS;
  clampGoalieYaw();
  applyGoaliePovLook();
}

let goaliePointerId = null;
function onGoaliePointerDown(e) {
  if (state.cameraPreset !== "goalie_pov" || state.dragEnabled) return;
  goaliePointerId = e.pointerId;
  canvas.setPointerCapture(e.pointerId);
}
function onGoaliePointerMove(e) {
  if (goaliePointerId !== e.pointerId || !state.goaliePov) return;
  state.goaliePov.yaw -= e.movementX * GOALIE_DRAG_SENS;
  clampGoalieYaw();
  applyGoaliePovLook();
}
function onGoaliePointerUp(e) {
  if (goaliePointerId !== e.pointerId) return;
  goaliePointerId = null;
  try {
    canvas.releasePointerCapture(e.pointerId);
  } catch {
    /* already released */
  }
}

canvas.addEventListener("wheel", onGoalieWheel, { passive: false });
canvas.addEventListener("pointerdown", onGoaliePointerDown);
canvas.addEventListener("pointermove", onGoaliePointerMove);
canvas.addEventListener("pointerup", onGoaliePointerUp);
canvas.addEventListener("pointercancel", onGoaliePointerUp);

function refreshReadout() {
  const lines = [];
  if (state.sceneData.puck) {
    const p = worldOf("puck");
    if (p) lines.push(`puck  (${p.x.toFixed(0)}, ${(-p.z).toFixed(0)})`);
  }
  state.sceneData.entities.forEach((e) => {
    const w = worldOf(e.id);
    if (w)
      lines.push(
        `${(e.label ?? e.role).padEnd(10)} (${w.x.toFixed(0)}, ${(-w.z).toFixed(0)})`,
      );
  });
  document.getElementById("readout").textContent = lines.join("\n");
}

function exportStill() {
  // Render one fresh frame, then read the canvas back as a PNG. The id of the
  // current scene becomes the filename so it lines up with the metadata in
  // content/still_image_of_the_day.json.
  resize();
  orbit.update();
  renderer.render(scene, camera);

  const id = state.sceneData?.id ?? "still";
  const link = document.createElement("a");
  link.download = `${id}.png`;
  link.href = canvas.toDataURL("image/png");
  document.body.appendChild(link);
  link.click();
  link.remove();
}

async function fetchScene(name) {
  const res = await fetch(`./scenes/${name}.json`);
  if (!res.ok) throw new Error(`Could not load scene ${name}`);
  return res.json();
}

function wireCameraBar(container) {
  PRESETS.forEach((p) => {
    const btn = document.createElement("button");
    btn.textContent = PRESET_LABELS[p];
    btn.dataset.cam = p;
    btn.onclick = () => setCamera(p);
    container.appendChild(btn);
  });
}

function buildUI() {
  wireCameraBar(document.getElementById("camera-bar"));
  const embedCam = document.getElementById("embed-camera-bar");
  if (embedCam) wireCameraBar(embedCam);

  const sel = document.getElementById("scene-select");
  SCENES.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    sel.appendChild(opt);
  });
  sel.onchange = () => fetchScene(sel.value).then(loadScene);

  const dragToggle = document.getElementById("drag-toggle");
  dragToggle.onclick = () => {
    state.dragEnabled = !state.dragEnabled;
    if (dragControls) dragControls.enabled = state.dragEnabled;
    dragToggle.classList.toggle("active", state.dragEnabled);
    dragToggle.textContent = state.dragEnabled
      ? "Move players: ON"
      : "Move players: OFF";
  };

  document.getElementById("reset-btn").onclick = () =>
    fetchScene(sel.value).then(loadScene);

  document.getElementById("export-btn").onclick = exportStill;

  ["ov-royal", "ov-shot", "ov-lanes"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.onchange = rebuildOverlays;
  });
}

function resize() {
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (canvas.width !== w || canvas.height !== h) {
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
}

function animate() {
  requestAnimationFrame(animate);
  resize();
  if (state.cameraPreset !== "goalie_pov") orbit.update();
  renderer.render(scene, camera);
}

async function discoverScenes() {
  try {
    const res = await fetch("/api/scenarios");
    if (res.ok) {
      const data = await res.json();
      const slugs = (data.scenarios || []).map((s) => s.slug).filter(Boolean);
      if (slugs.length) return slugs;
    }
  } catch {
    /* standalone viewer — no app API */
  }
  return [...SCENES_FALLBACK];
}

async function boot() {
  const params = new URLSearchParams(location.search);
  SCENES = await discoverScenes();
  const requested = params.get("scene");
  const startScene =
    requested && SCENES.includes(requested) ? requested : SCENES[0];
  if (params.get("hideui") === "1") document.body.classList.add("capture");
  if (params.get("embed") === "1") document.body.classList.add("embed");

  buildUI();
  document.getElementById("scene-select").value = startScene;
  fetchScene(startScene)
    .then((data) => {
      loadScene(data);
      const cam = params.get("camera");
      if (cam && PRESETS.includes(cam)) setCamera(cam);
    })
    .catch((err) => {
      document.getElementById("readout").textContent =
        `${err.message}\n\nRun a local server from viewer/ (see README).`;
    });
}

boot();
animate();
