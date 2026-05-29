// Camera presets. Each returns { position, target } in world space so the
// same scene can be viewed broadcast-style, from behind the net, the
// goalie's eyes, or straight overhead.

import { rinkToWorld } from "./rink.js";

function entityWorld(sceneData, role, fallbackX, fallbackY) {
  const e =
    sceneData.entities.find((n) => n.role === role) ??
    (role === "puck" ? sceneData.puck : null);
  if (e) return rinkToWorld(e.x, e.y, 0);
  return rinkToWorld(fallbackX, fallbackY, 0);
}

export const PRESETS = ["broadcast", "behind_net", "goalie_pov", "overhead"];

export const PRESET_LABELS = {
  broadcast: "Broadcast",
  behind_net: "Behind Net",
  goalie_pov: "Goalie POV",
  overhead: "Overhead",
};

export function cameraPose(preset, sceneData) {
  const puck = sceneData.puck
    ? rinkToWorld(sceneData.puck.x, sceneData.puck.y, 1)
    : entityWorld(sceneData, "carrier", 70, 10);
  const goalie = entityWorld(sceneData, "goalie", 87, 0);

  switch (preset) {
    case "overhead":
      return {
        position: rinkToWorld(60, 0, 150),
        target: rinkToWorld(62, 0, 0),
        fov: 45,
      };

    case "behind_net":
      return {
        position: rinkToWorld(106, 3, 14),
        target: rinkToWorld(55, 0, 2),
        fov: 60,
      };

    case "goalie_pov": {
      // Eye height (~5.2 ft) at the goalie, nudged slightly toward the play.
      const eye = goalie.clone();
      eye.y = 5.2;
      const aim = puck.clone();
      aim.y = 1.8;
      const forward = new THREE.Vector3().subVectors(aim, eye);
      const flat = forward.clone().setY(0);
      if (flat.lengthSq() > 0.01) {
        eye.add(flat.normalize().multiplyScalar(0.6));
      }
      return {
        position: eye,
        target: aim,
        forward: forward.normalize(),
        fov: 68,
        mode: "goalie_pov",
      };
    }

    case "broadcast":
    default:
      return {
        // Elevated, off the near boards around the top of the circles.
        position: rinkToWorld(40, 55, 78),
        target: rinkToWorld(74, 0, 0),
        fov: 50,
      };
  }
}
