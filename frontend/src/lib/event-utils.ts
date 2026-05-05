import type { NetworkEvent } from "./types";

export function getEventTime(e: NetworkEvent): string {
  return (e.timestamp || e.time || "") as string;
}
export function getSrc(e: NetworkEvent): string {
  return (e.src_ip || e.src || e.source || "—") as string;
}
export function getDst(e: NetworkEvent): string {
  return (e.dst_ip || e.dst || e.destination || "—") as string;
}
export function getProto(e: NetworkEvent): string {
  return (e.protocol || e.proto || "—") as string;
}
export function getDecision(e: NetworkEvent): string {
  return ((e.decision as string) || "—").toString().toUpperCase();
}
export function getConfidence(e: NetworkEvent): number | null {
  const c = e.confidence;
  if (typeof c === "number") return c;
  return null;
}
export function isAttack(e: NetworkEvent): boolean {
  const d = getDecision(e);
  return d === "BLOCK" || d === "ATTACK" || d === "ALERT" || d === "MALICIOUS";
}

export function formatTimeUTC(ts: string): string {
  if (!ts) return "—";
  const d = new Date(ts);
  if (isNaN(d.getTime())) return ts;
  return d.toISOString().replace("T", " ").replace(/\.\d+Z$/, "Z");
}
