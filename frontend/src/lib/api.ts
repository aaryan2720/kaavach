import axios, { AxiosInstance } from "axios";
import type {
  HealthStatus,
  LogFile,
  MonitorStatus,
  NetworkEvent,
  PredictRequest,
  PredictResponse,
  MetricsData,
  BatchIngestResponse,
  ModelReloadResponse,
} from "./types";

let baseURL = "http://localhost:8000";

export function setApiBaseUrl(url: string) {
  baseURL = url.replace(/\/$/, "");
  client = buildClient();
}

export function getApiBaseUrl() {
  return baseURL;
}

function buildClient(): AxiosInstance {
  return axios.create({ baseURL, timeout: 15000 });
}

let client = buildClient();

export const api = {
  health: async (): Promise<HealthStatus> => (await client.get("/health")).data,
  status: async (): Promise<MonitorStatus> => (await client.get("/monitor/status")).data,
  start: async (): Promise<MonitorStatus> => (await client.post("/monitor/start")).data,
  stop: async (): Promise<MonitorStatus> => (await client.post("/monitor/stop")).data,
  events: async (limit = 200): Promise<NetworkEvent[]> => {
    const res = await client.get("/monitor/events", { params: { limit } });
    const data = res.data;
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.events)) return data.events;
    return [];
  },
  predict: async (payload: PredictRequest): Promise<PredictResponse> =>
    (await client.post("/predict", payload)).data,
  logs: async (): Promise<LogFile[]> => {
    const res = await client.get("/logs");
    const data = res.data;
    if (Array.isArray(data)) {
      return data.map((d) => (typeof d === "string" ? { name: d } : d));
    }
    if (Array.isArray(data?.files)) {
      return data.files.map((d: unknown) => (typeof d === "string" ? { name: d } : d));
    }
    if (Array.isArray(data?.logs)) {
      return data.logs.map((d: unknown) => (typeof d === "string" ? { name: d } : d));
    }
    return [];
  },
  logsToday: async (): Promise<NetworkEvent[]> => {
    const res = await client.get("/logs/today");
    return parseJsonl(res.data);
  },
  logsFile: async (filename: string): Promise<NetworkEvent[]> => {
    const res = await client.get("/logs", { params: { file: filename } });
    return parseJsonl(res.data);
  },
  exportUrl: (filename: string) =>
    `${baseURL}/logs/export?filename=${encodeURIComponent(filename)}`,
  ingest: async (records: Array<Record<string, unknown>>): Promise<BatchIngestResponse> =>
    (await client.post("/ingest", { records })).data,
  metrics: async (minutes = 60): Promise<MetricsData> =>
    (await client.get("/metrics", { params: { minutes } })).data,
  reloadModel: async (): Promise<ModelReloadResponse> =>
    (await client.post("/model/reload")).data,
  debugLastPredict: async (): Promise<unknown> => (await client.get("/debug/last_predict")).data,
};

function parseJsonl(data: unknown): NetworkEvent[] {
  if (Array.isArray(data)) return data as NetworkEvent[];
  if (typeof data === "string") {
    return data
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean)
      .map((l) => {
        try {
          return JSON.parse(l) as NetworkEvent;
        } catch {
          return { reason: l } as NetworkEvent;
        }
      });
  }
  if (data && typeof data === "object" && Array.isArray((data as { events?: unknown }).events)) {
    return (data as { events: NetworkEvent[] }).events;
  }
  return [];
}
