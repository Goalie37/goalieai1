// Player / puck mesh builders. Skaters are low-poly articulated figures
// (legs in a stride, leaning torso, arms onto a stick); goalies get pads,
// blocker, glove and a mask. Original geometry — no copyrighted assets.

import * as THREE from "three";
import { rinkToWorld } from "./rink.js";

const TEAM_COLORS = {
  offense: 0x1f2d3d, // dark jerseys (attacking)
  defense: 0xeef2f5, // light jerseys (defending)
  goalie: 0xf6c945, // distinct so the goalie always reads clearly
};
const PANTS = 0x12181f;
const SKIN = 0xd9a679;
const HELMET = 0x10161d;
const STICK_SHAFT = 0x6b4423;

const PLAYER_HEIGHT = 6.0; // feet, head-to-ice

function mat(color, opts = {}) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.6,
    metalness: 0.05,
    ...opts,
  });
}

// Cylinder spanning two points — used for limbs so a stride/lean is easy.
function bone(a, b, radius, material) {
  const dir = new THREE.Vector3().subVectors(b, a);
  const len = dir.length() || 0.01;
  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(radius, radius, len, 8),
    material,
  );
  mesh.position.copy(a).addScaledVector(dir, 0.5);
  mesh.quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    dir.clone().normalize(),
  );
  mesh.castShadow = true;
  return mesh;
}

function v(x, y, z) {
  return new THREE.Vector3(x, y, z);
}

// Hockey stick from the hands down to a blade flat on the ice.
function makeStick(stickSide, grip) {
  const group = new THREE.Group();
  const z = stickSide === "right" ? 1.0 : -1.0;
  const blade = v(4.4, 0.18, z * 1.2);
  group.add(bone(grip, blade, 0.11, mat(STICK_SHAFT, { roughness: 0.7 })));
  const bladeMesh = new THREE.Mesh(
    new THREE.BoxGeometry(1.4, 0.5, 0.18),
    mat(0x222222, { roughness: 0.8 }),
  );
  bladeMesh.position.set(blade.x + 0.4, 0.3, blade.z);
  bladeMesh.castShadow = true;
  group.add(bladeMesh);
  return group;
}

function buildSkater(group, color, stickSide) {
  const jersey = mat(color);
  const pants = mat(PANTS);
  const skin = mat(SKIN, { roughness: 0.5 });

  // Legs in a slight stride (front leg forward in +x).
  const hipL = v(-0.1, 2.6, -0.5);
  const hipR = v(-0.1, 2.6, 0.5);
  const skateL = v(-0.6, 0.25, -0.6); // trailing leg
  const skateR = v(0.7, 0.25, 0.6); // lead leg
  group.add(bone(hipL, skateL, 0.32, pants));
  group.add(bone(hipR, skateR, 0.32, pants));
  for (const s of [skateL, skateR]) {
    const skate = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.35, 0.45), mat(0x111111));
    skate.position.set(s.x + 0.3, 0.18, s.z);
    skate.castShadow = true;
    group.add(skate);
  }

  // Pelvis + leaning torso.
  const pelvis = v(-0.1, 2.7, 0);
  const chest = v(0.7, 4.5, 0); // forward lean
  group.add(bone(pelvis, chest, 0.85, jersey));

  // Shoulders.
  const shoulders = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.55, 1.7, 4, 8),
    jersey,
  );
  shoulders.rotation.x = Math.PI / 2;
  shoulders.position.copy(chest);
  shoulders.castShadow = true;
  group.add(shoulders);

  // Arms reaching forward onto the stick grip.
  const grip = v(2.2, 2.7, stickSide === "right" ? 0.3 : -0.3);
  group.add(bone(v(chest.x, chest.y, -1.0), grip, 0.26, jersey));
  group.add(bone(v(chest.x, chest.y, 1.0), grip, 0.26, jersey));

  // Neck + head + helmet.
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.52, 14, 14), skin);
  head.position.set(0.95, 5.2, 0);
  head.castShadow = true;
  group.add(head);
  const helmet = new THREE.Mesh(
    new THREE.SphereGeometry(0.62, 14, 14, 0, Math.PI * 2, 0, Math.PI * 0.62),
    mat(HELMET, { roughness: 0.4 }),
  );
  helmet.position.set(0.95, 5.25, 0);
  group.add(helmet);

  group.add(makeStick(stickSide, grip));
}

function buildGoalie(group, color) {
  const pad = mat(color, { roughness: 0.7 });
  const dark = mat(PANTS);
  const skin = mat(SKIN, { roughness: 0.5 });

  // Wide leg pads, slightly crouched.
  for (const z of [-0.95, 0.95]) {
    const legpad = new THREE.Mesh(new THREE.BoxGeometry(1.7, 3.0, 0.95), pad);
    legpad.position.set(0.2, 1.55, z);
    legpad.castShadow = true;
    group.add(legpad);
    const skate = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.4, 0.7), mat(0x111111));
    skate.position.set(0.35, 0.2, z);
    group.add(skate);
  }

  // Chest protector / body, hunched forward.
  const torso = new THREE.Mesh(new THREE.BoxGeometry(1.4, 2.2, 2.6), pad);
  torso.position.set(0.05, 3.7, 0);
  torso.castShadow = true;
  group.add(torso);

  // Catch glove (one side) + blocker (other side).
  const glove = new THREE.Mesh(new THREE.BoxGeometry(1.0, 1.1, 1.0), dark);
  glove.position.set(0.9, 3.4, -1.7);
  glove.castShadow = true;
  group.add(glove);
  const blocker = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.3, 0.7), dark);
  blocker.position.set(0.9, 3.4, 1.7);
  blocker.castShadow = true;
  group.add(blocker);

  // Goalie stick across the front.
  const gstick = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.5, 3.2), mat(STICK_SHAFT, { roughness: 0.7 }));
  gstick.position.set(1.5, 0.4, 0.5);
  group.add(gstick);

  // Head + mask.
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.6, 14, 14), skin);
  head.position.set(0.1, 5.0, 0);
  head.castShadow = true;
  group.add(head);
  const mask = new THREE.Mesh(
    new THREE.SphereGeometry(0.7, 14, 14, 0, Math.PI * 2, 0, Math.PI * 0.7),
    mat(0xf4f6f8, { roughness: 0.4 }),
  );
  mask.position.set(0.1, 5.05, 0);
  group.add(mask);
}

export function buildPlayer(entity) {
  const group = new THREE.Group();
  group.name = entity.id;
  group.userData = { ...entity, kind: "player" };

  const color = TEAM_COLORS[entity.team] ?? 0x888888;
  if (entity.role === "goalie") {
    buildGoalie(group, color);
  } else {
    buildSkater(group, color, entity.stick ?? "left");
  }

  group.position.copy(rinkToWorld(entity.x, entity.y, 0));

  // facing: degrees, 0 points toward +rink-x (the attacking net).
  if (typeof entity.facing === "number") {
    group.rotation.y = -THREE.MathUtils.degToRad(entity.facing);
  }
  return group;
}

export function buildPuck(puck) {
  const group = new THREE.Group();
  group.name = "puck";
  group.userData = { ...puck, kind: "puck" };
  const disc = new THREE.Mesh(
    new THREE.CylinderGeometry(0.9, 0.9, 0.4, 20),
    mat(0x0a0a0a, { roughness: 0.4 }),
  );
  disc.position.y = 0.2;
  disc.castShadow = true;
  group.add(disc);
  group.position.copy(rinkToWorld(puck.x, puck.y, 0));
  return group;
}
