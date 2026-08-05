import maplibregl, {
  type CustomLayerInterface,
  type CustomRenderMethod,
  type Map as MapLibreMap,
} from "maplibre-gl";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

import { createProceduralDrone, setDroneArmed, setDroneSelected } from "./createProceduralDrone";
import { type DroneVisualId, visualForAdapter } from "./droneVisualCatalog";
import { BAYLANDS_CENTER } from "./mapDefaults";
import type { AdapterType, NormalizedTelemetry } from "@/types/telemetry";

/** Visual scale ≈ true size; slight boost so ~0.5 m span stays readable at zoom 18. */
const DISPLAY_METERS_SCALE = 2.8;

export interface DronePoseUpdate {
  id: string;
  lng: number;
  lat: number;
  altM: number;
  headingDeg: number;
  armed: boolean;
  selected: boolean;
  adapter: AdapterType;
  visualId?: DroneVisualId;
  gltfUrl?: string | null;
}

/**
 * MapLibre custom 3D layer — Y-up Three.js scene + MapLibre mercator matrix
 * (same pattern as MapLibre's official three.js example; no double scene rotate).
 */
export class DroneFleetLayer implements CustomLayerInterface {
  id = "drone-fleet-3d";
  type = "custom" as const;
  renderingMode = "3d" as const;

  private map: MapLibreMap | null = null;
  private camera = new THREE.Camera();
  private scene = new THREE.Scene();
  private renderer: THREE.WebGLRenderer | null = null;
  private drones = new Map<string, THREE.Group>();
  private loader = new GLTFLoader();
  private propSpin = 0;
  private pending: DronePoseUpdate[] = [];
  private ready = false;

  constructor(private sceneOrigin: [number, number] = BAYLANDS_CENTER) {}

  onAdd(map: MapLibreMap, gl: WebGLRenderingContext | WebGL2RenderingContext): void {
    this.map = map;
    this.ready = true;

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const sun = new THREE.DirectionalLight(0xffffff, 1.0);
    sun.position.set(50, 80, 30);
    this.scene.add(sun);
    const fill = new THREE.DirectionalLight(0x93c5fd, 0.4);
    fill.position.set(-40, 30, -20);
    this.scene.add(fill);

    this.renderer = new THREE.WebGLRenderer({
      canvas: map.getCanvas(),
      context: gl as WebGLRenderingContext & WebGL2RenderingContext,
      antialias: true,
    });
    this.renderer.autoClear = false;

    if (this.pending.length) {
      this.sync(this.pending);
      this.pending = [];
    }
  }

  onRemove(): void {
    this.ready = false;
    for (const g of this.drones.values()) {
      this.scene.remove(g);
      disposeObject(g);
    }
    this.drones.clear();
    this.renderer?.dispose();
    this.renderer = null;
    this.map = null;
  }

  sync(poses: DronePoseUpdate[]): void {
    if (!this.ready) {
      this.pending = poses;
      return;
    }

    const active = new Set(poses.map((p) => p.id));
    for (const [id, group] of this.drones) {
      if (!active.has(id)) {
        this.scene.remove(group);
        disposeObject(group);
        this.drones.delete(id);
      }
    }

    for (const pose of poses) {
      let group = this.drones.get(pose.id);
      const visual = pose.visualId ?? visualForAdapter(pose.adapter);
      if (!group) {
        group = new THREE.Group();
        group.name = pose.id;
        this.drones.set(pose.id, group);
        this.scene.add(group);
        void this.attachVisual(group, visual, pose.gltfUrl ?? null);
      }
      setDroneSelected(group, pose.selected);
      setDroneArmed(group, pose.armed);

      // Three.js Y-up: x=east, y=up, z=south (flip north → -z). Layer matrix rotates to map space.
      const local = this.toLocalYUp(pose.lng, pose.lat, pose.altM);
      group.position.set(local.x, local.y, local.z);
      const headingRad = ((pose.headingDeg ?? 0) * Math.PI) / 180;
      // Nose along +X in mesh; yaw around up (Y)
      group.rotation.set(0, -headingRad, 0);

      group.scale.setScalar(DISPLAY_METERS_SCALE);
    }

    this.map?.triggerRepaint();
  }

  render: CustomRenderMethod = (_gl, matrix) => {
    if (!this.renderer || !this.map) return;

    this.propSpin += 0.4;
    for (const group of this.drones.values()) {
      group.traverse((obj) => {
        if (obj.name === "prop") obj.rotation.y = this.propSpin;
      });
    }

    const originMerc = maplibregl.MercatorCoordinate.fromLngLat(this.sceneOrigin, 0);
    const meterScale = originMerc.meterInMercatorCoordinateUnits();
    const rotateX = new THREE.Matrix4().makeRotationAxis(
      new THREE.Vector3(1, 0, 0),
      Math.PI / 2,
    );

    const m = new THREE.Matrix4().fromArray(matrix as unknown as number[]);
    const l = new THREE.Matrix4()
      .makeTranslation(originMerc.x, originMerc.y, originMerc.z)
      .scale(new THREE.Vector3(meterScale, -meterScale, meterScale))
      .multiply(rotateX);

    this.camera.projectionMatrix = m.multiply(l);
    this.renderer.resetState();
    this.renderer.render(this.scene, this.camera);
    this.map.triggerRepaint();
  };

  private toLocalYUp(lng: number, lat: number, altM: number): THREE.Vector3 {
    const from = maplibregl.MercatorCoordinate.fromLngLat(this.sceneOrigin, 0);
    const to = maplibregl.MercatorCoordinate.fromLngLat([lng, lat], Math.max(altM, 1));
    const m = from.meterInMercatorCoordinateUnits();
    // mercator delta → metres: east, up, south
    return new THREE.Vector3(
      (to.x - from.x) / m,
      (to.z - from.z) / m,
      (to.y - from.y) / m,
    );
  }

  private async attachVisual(
    parent: THREE.Group,
    visual: DroneVisualId,
    gltfUrl: string | null,
  ): Promise<void> {
    while (parent.children.length) {
      const child = parent.children[0]!;
      parent.remove(child);
      disposeObject(child);
    }

    if (gltfUrl) {
      try {
        const gltf = await this.loader.loadAsync(gltfUrl);
        const model = gltf.scene;
        const box = new THREE.Box3().setFromObject(model);
        const size = new THREE.Vector3();
        box.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z) || 1;
        model.scale.multiplyScalar(0.5 / maxDim);
        parent.add(model);
        this.map?.triggerRepaint();
        return;
      } catch {
        // procedural fallback
      }
    }

    parent.add(createProceduralDrone(visual));
    this.map?.triggerRepaint();
  }
}

function disposeObject(obj: THREE.Object3D): void {
  obj.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.geometry.dispose();
      const mat = child.material;
      if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
      else mat.dispose();
    }
  });
}

export function telemetryToPoses(
  telemetryByDrone: Record<string, NormalizedTelemetry>,
  selectedDroneId: string | null | undefined,
): DronePoseUpdate[] {
  const poses: DronePoseUpdate[] = [];
  for (const [id, sample] of Object.entries(telemetryByDrone)) {
    const lat = sample.gps.position?.latitude_deg;
    const lon = sample.gps.position?.longitude_deg;
    if (lat == null || lon == null) continue;
    const alt =
      sample.relative_altitude_m ??
      sample.gps.position?.relative_altitude_m ??
      0;
    poses.push({
      id,
      lng: lon,
      lat,
      altM: Math.max(alt, 1.5),
      headingDeg: sample.heading_deg ?? 0,
      armed: sample.armed,
      selected: id === selectedDroneId,
      adapter: sample.source,
    });
  }
  return poses;
}
