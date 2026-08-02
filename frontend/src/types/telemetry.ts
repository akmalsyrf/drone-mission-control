export type AdapterType = "px4" | "gazebo" | "dji_cloud" | "simulated";

export type ConnectionStatus =
  | "registered"
  | "connecting"
  | "online"
  | "offline"
  | "error";

export type FlightMode =
  | "UNKNOWN"
  | "MANUAL"
  | "ALTCTL"
  | "POSCTL"
  | "AUTO"
  | "OFFBOARD"
  | "RTL"
  | "LAND"
  | "TAKEOFF"
  | "HOLD"
  | "MISSION";

export interface Drone {
  id: string;
  name: string;
  adapter_type: AdapterType;
  connection_uri: string;
  connection_status: ConnectionStatus;
  last_heartbeat: string | null;
  current_mission_id: string | null;
  metadata: Record<string, unknown>;
}

export interface GeoPoint {
  latitude_deg: number;
  longitude_deg: number;
  absolute_altitude_m: number | null;
  relative_altitude_m: number | null;
}

export interface GpsFix {
  position: GeoPoint | null;
  num_satellites: number | null;
  fix_type: number | null;
}

export interface BatteryState {
  remaining_percent: number | null;
  voltage_v: number | null;
}

export interface NormalizedTelemetry {
  drone_id: string;
  timestamp: string;
  gps: GpsFix;
  battery: BatteryState;
  heading_deg: number | null;
  altitude_m: number | null;
  relative_altitude_m: number | null;
  flight_mode: FlightMode;
  armed: boolean;
  speed_m_s: number | null;
  source: AdapterType;
}

export type VehicleCommand = "arm" | "disarm" | "rtl" | "hold" | "takeoff" | "land";
