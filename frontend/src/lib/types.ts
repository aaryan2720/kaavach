export type Decision = "ALLOW" | "BLOCK" | "ALERT" | "attack" | "normal" | "ATTACK" | string;

export interface NetworkEvent {
  timestamp?: string;
  time?: string;
  src_ip?: string;
  dst_ip?: string;
  src?: string;
  dst?: string;
  source?: string;
  destination?: string;
  protocol?: string;
  proto?: string;
  decision?: Decision;
  reason?: string;
  confidence?: number;
  [key: string]: unknown;
}

export interface MonitorStatus {
  running: boolean;
  backend?: string;
  events_buffered?: number;
  backend_available?: boolean;
  buffered_events?: number;
  model_version?: string;
  uptime_seconds?: number;
  [key: string]: unknown;
}

export interface MetricsData {
  per_minute: Record<string, { total: number; attacks: number }>;
  total_events: number;
  total_attacks: number;
}

export interface BatchIngestResponse {
  ok: boolean;
  result: { count: number; error?: string };
}

export interface ModelReloadResponse {
  ok: { success: boolean; message: string };
}

export interface HealthStatus {
  status: string;
  version?: string;
  [key: string]: unknown;
}

export interface PredictRequest {
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: string;
  packet_size: number;
  duration: number;
  packet_count: number;
  byte_count: number;
}

export interface PredictResponse {
  decision: Decision;
  confidence: number;
  reason?: string;
  raw?: unknown;
  [key: string]: unknown;
}

export interface LogFile {
  name: string;
  size?: number;
  modified?: string;
}
