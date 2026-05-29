// Low-poly NHL rink built in three.js.
// Coordinate convention matches MoneyPuck shot data (feet):
//   rink x  = north-south, attacking net at x = +89
//   rink y  = east-west, center ice at y = 0, boards at y = ±42.5
// World mapping: world.x = rink.x, world.z = -rink.y, up = +y.

import * as THREE from "three";

export const RINK = {
  halfLength: 100, // x: -100..100
  halfWidth: 42.5, // y: -42.5..42.5
  blueLine: 25, // distance of blue lines from center
  goalLine: 89, // distance of goal line from center
  faceoffDotX: 69,
  faceoffDotY: 22,
  faceoffRadius: 15,
  creaseRadius: 6,
  cornerRadius: 28,
  netWidth: 6, // 72 in
  netHeight: 4,
  netDepth: 3.5,
};

export function rinkToWorld(x, y, height = 0) {
  return new THREE.Vector3(x, height, -y);
}

function lineStrip(points, color, y = 0.06, lineWidth = 1) {
  const geo = new THREE.BufferGeometry().setFromPoints(
    points.map((p) => rinkToWorld(p[0], p[1], y)),
  );
  const mat = new THREE.LineBasicMaterial({ color, linewidth: lineWidth });
  return new THREE.Line(geo, mat);
}

function paintStripe(xCenter, color, halfWidth = RINK.halfWidth, thickness = 1) {
  const geo = new THREE.PlaneGeometry(thickness, halfWidth * 2);
  const mat = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.85,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.copy(rinkToWorld(xCenter, 0, 0.04));
  return mesh;
}

function faceoffCircle(cx, cy, color = 0xc0392b) {
  const group = new THREE.Group();
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(RINK.faceoffRadius - 0.4, RINK.faceoffRadius, 48),
    new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide }),
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.copy(rinkToWorld(cx, cy, 0.05));
  group.add(ring);
  const dot = new THREE.Mesh(
    new THREE.CircleGeometry(1, 24),
    new THREE.MeshBasicMaterial({ color }),
  );
  dot.rotation.x = -Math.PI / 2;
  dot.position.copy(rinkToWorld(cx, cy, 0.05));
  group.add(dot);
  return group;
}

function crease(goalX) {
  const shape = new THREE.Shape();
  shape.absarc(0, 0, RINK.creaseRadius, Math.PI / 2, -Math.PI / 2, true);
  const geo = new THREE.ShapeGeometry(shape, 32);
  const mat = new THREE.MeshBasicMaterial({
    color: 0x4a90d9,
    transparent: true,
    opacity: 0.45,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.rotation.x = -Math.PI / 2;
  // Open side of the half-disc faces center ice (toward -x from the net).
  mesh.rotation.z = Math.PI;
  mesh.position.copy(rinkToWorld(goalX, 0, 0.05));
  return mesh;
}

function net(goalX) {
  const group = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ color: 0xd62828, metalness: 0.1, roughness: 0.6 });
  const post = new THREE.CylinderGeometry(0.18, 0.18, RINK.netHeight, 8);
  const halfW = RINK.netWidth / 2;

  const leftPost = new THREE.Mesh(post, mat);
  leftPost.position.copy(rinkToWorld(goalX, halfW, RINK.netHeight / 2));
  const rightPost = new THREE.Mesh(post, mat);
  rightPost.position.copy(rinkToWorld(goalX, -halfW, RINK.netHeight / 2));
  group.add(leftPost, rightPost);

  const crossbar = new THREE.Mesh(
    new THREE.CylinderGeometry(0.18, 0.18, RINK.netWidth, 8),
    mat,
  );
  crossbar.rotation.x = Math.PI / 2;
  crossbar.position.copy(rinkToWorld(goalX, 0, RINK.netHeight));
  group.add(crossbar);

  // Mesh netting (semi-transparent), angled back toward the boards (+x).
  const netting = new THREE.Mesh(
    new THREE.PlaneGeometry(RINK.netWidth, RINK.netHeight),
    new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.18,
      side: THREE.DoubleSide,
    }),
  );
  netting.position.copy(rinkToWorld(goalX + RINK.netDepth, 0, RINK.netHeight / 2));
  netting.rotation.y = Math.PI / 2;
  group.add(netting);
  return group;
}

function boards() {
  const w = RINK.halfLength;
  const h = RINK.halfWidth;
  const r = RINK.cornerRadius;
  const shape = new THREE.Shape();
  shape.moveTo(-w + r, -h);
  shape.lineTo(w - r, -h);
  shape.quadraticCurveTo(w, -h, w, -h + r);
  shape.lineTo(w, h - r);
  shape.quadraticCurveTo(w, h, w - r, h);
  shape.lineTo(-w + r, h);
  shape.quadraticCurveTo(-w, h, -w, h - r);
  shape.lineTo(-w, -h + r);
  shape.quadraticCurveTo(-w, -h, -w + r, -h);

  const points = shape.getPoints(80).map((p) => rinkToWorld(p.x, p.y, 0));
  const top = points.map((p) => p.clone().setY(3.5));
  const geo = new THREE.BufferGeometry().setFromPoints([...points, ...top.reverse()]);
  const mat = new THREE.LineBasicMaterial({ color: 0xdfe6e9 });
  const loop = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(top),
    mat,
  );
  const base = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(points),
    mat,
  );
  const group = new THREE.Group();
  group.add(loop, base);
  return group;
}

function iceSurface() {
  const w = RINK.halfLength;
  const h = RINK.halfWidth;
  const r = RINK.cornerRadius;
  const shape = new THREE.Shape();
  shape.moveTo(-w + r, -h);
  shape.lineTo(w - r, -h);
  shape.quadraticCurveTo(w, -h, w, -h + r);
  shape.lineTo(w, h - r);
  shape.quadraticCurveTo(w, h, w - r, h);
  shape.lineTo(-w + r, h);
  shape.quadraticCurveTo(-w, h, -w, h - r);
  shape.lineTo(-w, -h + r);
  shape.quadraticCurveTo(-w, -h, -w + r, -h);
  const geo = new THREE.ShapeGeometry(shape, 12);
  const mat = new THREE.MeshStandardMaterial({
    color: 0xf3f8fc,
    roughness: 0.35,
    metalness: 0.05,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = 0;
  mesh.receiveShadow = true;
  return mesh;
}

export function buildRink() {
  const rink = new THREE.Group();
  rink.name = "rink";

  rink.add(iceSurface());
  rink.add(boards());

  // Center red line + center faceoff circle.
  rink.add(paintStripe(0, 0xc0392b, RINK.halfWidth, 1));
  rink.add(faceoffCircle(0, 0, 0x2d6cdf));

  // Blue lines.
  rink.add(paintStripe(-RINK.blueLine, 0x2d6cdf, RINK.halfWidth, 1.2));
  rink.add(paintStripe(RINK.blueLine, 0x2d6cdf, RINK.halfWidth, 1.2));

  // Goal lines (thin, red) — only span between the boards arcs.
  rink.add(paintStripe(RINK.goalLine, 0xc0392b, RINK.halfWidth - 14, 0.4));
  rink.add(paintStripe(-RINK.goalLine, 0xc0392b, RINK.halfWidth - 14, 0.4));

  // Offensive-zone faceoff circles + creases + nets (both ends drawn).
  rink.add(faceoffCircle(RINK.faceoffDotX, RINK.faceoffDotY));
  rink.add(faceoffCircle(RINK.faceoffDotX, -RINK.faceoffDotY));
  rink.add(faceoffCircle(-RINK.faceoffDotX, RINK.faceoffDotY));
  rink.add(faceoffCircle(-RINK.faceoffDotX, -RINK.faceoffDotY));

  rink.add(crease(RINK.goalLine));
  rink.add(net(RINK.goalLine));

  return rink;
}
