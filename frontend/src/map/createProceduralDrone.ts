import * as THREE from "three";

import type { DroneVisualId } from "./droneVisualCatalog";

/** Realistic X500-ish palette (not UI accent colors). */
const BODY = 0x1c1c1e;
const ARM = 0x2a2a2e;
const MOTOR = 0x3f3f46;
const CANOPY = 0x52525b;
const PROP = 0x94a3b8;
const LED_FRONT = 0xf97316;
const LED_REAR = 0xef4444;

/**
 * Procedural low-poly quadcopter — Three.js Y-up, +X nose (~0.5 m span).
 */
export function createProceduralDrone(visual: DroneVisualId): THREE.Group {
  const root = new THREE.Group();
  root.name = `drone-${visual}`;

  const bodyMat = new THREE.MeshStandardMaterial({
    color: BODY,
    metalness: 0.65,
    roughness: 0.4,
  });
  const armMat = new THREE.MeshStandardMaterial({
    color: ARM,
    metalness: 0.55,
    roughness: 0.45,
  });
  const motorMat = new THREE.MeshStandardMaterial({
    color: MOTOR,
    metalness: 0.7,
    roughness: 0.35,
  });
  const canopyMat = new THREE.MeshStandardMaterial({
    color: CANOPY,
    metalness: 0.2,
    roughness: 0.55,
  });
  const propMat = new THREE.MeshStandardMaterial({
    color: PROP,
    metalness: 0.05,
    roughness: 0.7,
    transparent: true,
    opacity: 0.55,
  });
  const ledFrontMat = new THREE.MeshStandardMaterial({
    color: LED_FRONT,
    emissive: LED_FRONT,
    emissiveIntensity: 0.55,
    metalness: 0.1,
    roughness: 0.4,
  });
  const ledRearMat = new THREE.MeshStandardMaterial({
    color: LED_REAR,
    emissive: LED_REAR,
    emissiveIntensity: 0.4,
    metalness: 0.1,
    roughness: 0.4,
  });

  const scale = visual === "x500" ? 1.1 : visual === "iris" ? 1.0 : 0.92;
  const armLen = visual === "iris" ? 0.28 : 0.24;
  const armSpread = visual === "iris" ? 0.2 : 0.17;

  const body = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.06, 0.2), bodyMat);
  body.position.y = 0.035;
  root.add(body);

  const canopy = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.04, 0.13), canopyMat);
  canopy.position.set(0.015, 0.08, 0);
  root.add(canopy);

  const armGeom = new THREE.BoxGeometry(armLen, 0.018, 0.03);
  const motorGeom = new THREE.CylinderGeometry(0.032, 0.036, 0.035, 12);
  const propGeom = new THREE.CylinderGeometry(0.11, 0.11, 0.008, 20);

  const corners: [number, number][] = [
    [armSpread, armSpread],
    [armSpread, -armSpread],
    [-armSpread, armSpread],
    [-armSpread, -armSpread],
  ];

  for (const [x, z] of corners) {
    const arm = new THREE.Mesh(armGeom, armMat);
    arm.position.set(x * 0.45, 0.04, z * 0.45);
    arm.rotation.y = Math.atan2(z, x);
    root.add(arm);

    const motor = new THREE.Mesh(motorGeom, motorMat);
    motor.position.set(x, 0.055, z);
    root.add(motor);

    const prop = new THREE.Mesh(propGeom, propMat);
    prop.position.set(x, 0.08, z);
    prop.name = "prop";
    root.add(prop);
  }

  // Front (orange) + rear (red) LEDs — typical UAV lights, not UI cyan
  const noseLed = new THREE.Mesh(new THREE.SphereGeometry(0.018, 10, 10), ledFrontMat);
  noseLed.position.set(0.12, 0.045, 0);
  noseLed.name = "led-front";
  root.add(noseLed);

  const tailLed = new THREE.Mesh(new THREE.SphereGeometry(0.015, 10, 10), ledRearMat);
  tailLed.position.set(-0.11, 0.045, 0);
  root.add(tailLed);

  // Selection ring (hidden by default) — toggled without recoloring the airframe
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.32, 0.38, 48),
    new THREE.MeshBasicMaterial({
      color: 0x5eead4,
      transparent: true,
      opacity: 0.85,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.01;
  ring.name = "select-ring";
  ring.visible = false;
  root.add(ring);

  root.scale.setScalar(scale);
  return root;
}

export function setDroneSelected(root: THREE.Group, selected: boolean): void {
  const ring = root.getObjectByName("select-ring");
  if (ring) ring.visible = selected;
}

export function setDroneArmed(root: THREE.Group, armed: boolean): void {
  const led = root.getObjectByName("led-front");
  if (!(led instanceof THREE.Mesh)) return;
  const mat = led.material;
  if (mat instanceof THREE.MeshStandardMaterial) {
    mat.emissiveIntensity = armed ? 0.95 : 0.55;
  }
}
