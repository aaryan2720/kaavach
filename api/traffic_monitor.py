from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
import concurrent.futures
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from inference import KaavachPredictor

try:
    from scapy.all import ICMP, IP, TCP, UDP, conf, sniff  # type: ignore

    SCAPY_AVAILABLE = True
except Exception:
    SCAPY_AVAILABLE = False


@dataclass
class MonitorEvent:
    timestamp: str
    src_ip: str
    dst_ip: str
    protocol: str
    decision: str
    confidence: float
    reason: str
    length: int = 0
    src_port: int | None = None
    dst_port: int | None = None


class TrafficMonitor:
    def __init__(self, predictor: KaavachPredictor, logs_dir: str = "logs", iface: str | None = None) -> None:
        self.predictor = predictor
        self.iface = iface
        # On Windows, default to "Wi-Fi" if not specified, as it's the most common active interface
        if self.iface is None and SCAPY_AVAILABLE and sys.platform == "win32":
            self.iface = "Wi-Fi"
            
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._events: deque[dict[str, Any]] = deque(maxlen=500)
        self._icmp_window: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=50))
        self._lock = threading.Lock()
        # Executor used to offload model inference so sniff thread stays responsive
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        # simple in-memory metrics: counts per minute
        self._metrics: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "attacks": 0})
        self._start_time: float | None = None
        self._total_processed: int = 0
        self._attack_alert_counter = 0
        self._alert_threshold = 5
        
        # SMTP Configuration (Placeholder - fill these in!)
        self.smtp_config = {
            "enabled": True, # Set to True to enable alerts
            "host": "smtp.gmail.com",
            "port": 587,
            "user": "shreyasbawaskar0812@gmail.com",
            "pass": "slna tota kgbg tsdl",
            "recipient": "aaryanchoudhari326@gmail.com"
        }

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def backend(self) -> str:
        return "scapy" if SCAPY_AVAILABLE else "unavailable"

    def start(self) -> dict[str, Any]:
        if not SCAPY_AVAILABLE:
            return {
                "started": False,
                "reason": "scapy_not_available",
                "message": "Scapy/Npcap is required for live sniffing on Windows.",
            }

        if self._running:
            return {"started": True, "message": "Monitor already running."}

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._sniff_loop, daemon=True)
        self._start_time = time.time()
        self._thread.start()
        self._running = True
        return {"started": True, "message": "Traffic monitor started."}

    def stop(self) -> dict[str, Any]:
        if not self._running:
            return {"stopped": True, "message": "Monitor already stopped."}

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        # shutdown executor to free threads
        try:
            self._executor.shutdown(wait=False)
        except Exception:
            pass
        self._running = False
        self._start_time = None
        return {"stopped": True, "message": "Traffic monitor stopped."}

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "backend": self.backend,
            "backend_available": SCAPY_AVAILABLE,
            "events_buffered": len(self._events),
            "buffered_events": len(self._events),
            "uptime_seconds": int(time.time() - self._start_time) if self._start_time else 0,
            "total_processed": self._total_processed,
            "interface": self.iface,
            "model_name": self.predictor.model_name,
            "threshold": self.predictor.threshold,
        }

    def latest_events(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        return list(self._events)[-limit:]

    def _get_log_file_path(self) -> Path:
        """Get today's log file path."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.logs_dir / f"{today}_traffic.jsonl"

    def _save_event_to_disk(self, event_dict: dict[str, Any]) -> None:
        """Append event to daily JSONL log file."""
        try:
            log_file = self._get_log_file_path()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict) + "\n")
        except Exception as e:
            print(f"Warning: Failed to save event to log file: {e}")

    def _sniff_loop(self) -> None:
        print(f"DEBUG: Starting sniff loop on interface: {self.iface or 'default'}")
        while not self._stop_event.is_set():
            try:
                sniff(
                    iface=self.iface,
                    filter="ip",
                    prn=self._handle_packet,
                    store=False,
                    timeout=1,
                )
            except Exception as e:
                print(f"Sniff error: {e}")
                time.sleep(2)
        self._running = False

    def _handle_packet(self, packet: Any) -> None:
        if IP not in packet:
            return

        now_ts = time.time()
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        proto_num = int(packet[IP].proto)
        proto_map = {1: "icmp", 6: "tcp", 17: "udp"}
        proto = proto_map.get(proto_num, str(proto_num))

        # Console logging for real-time verification
        print(f"📡 [Sniff] {src_ip} -> {dst_ip} ({proto}) | {int(len(packet))} bytes")

        ttl = int(getattr(packet[IP], "ttl", 64))
        length = int(len(packet))

        src_port = None
        dst_port = None
        if TCP in packet:
            src_port = int(packet[TCP].sport)
            dst_port = int(packet[TCP].dport)
        elif UDP in packet:
            src_port = int(packet[UDP].sport)
            dst_port = int(packet[UDP].dport)

        # Minimal flow-like feature map (remaining features default to zero/missing in predictor).
        features = {
            "proto": proto,
            "service": "-",
            "state": "INT",
            "dur": 0.01,
            "spkts": 1,
            "dpkts": 0,
            "sbytes": length,
            "dbytes": 0,
            "rate": 100,
            "sttl": ttl,
            "dttl": 0,
        }

        # Offload prediction and event creation to executor so sniff loop stays responsive
        try:
            self._executor.submit(
                self._process_packet,
                now_ts,
                src_ip,
                dst_ip,
                proto,
                features,
                packet,
                length,
                src_port,
                dst_port,
            )
        except Exception:
            # Best-effort: if executor rejects, fall back to synchronous processing
            self._process_packet(now_ts, src_ip, dst_ip, proto, features, packet, length, src_port, dst_port)

    def _process_packet(
        self,
        now_ts: float,
        src_ip: str,
        dst_ip: str,
        proto: str,
        features: dict[str, Any],
        packet: Any,
        length: int,
        src_port: int | None,
        dst_port: int | None,
    ) -> None:
        # Run model inference
        try:
            pred = self.predictor.predict_one(features)
        except Exception:
            pred = {"decision": "normal", "confidence": 0.0}

        reason = "model_inference"
        decision = pred.get("decision", "normal")
        confidence = float(pred.get("confidence", 0.0))

        # Explicit ping detector: ICMP echo-request burst from same source.
        if ICMP in packet and int(packet[ICMP].type) == 8:
            with self._lock:
                q = self._icmp_window[src_ip]
                q.append(now_ts)
                while q and now_ts - q[0] > 10:
                    q.popleft()
                if len(q) >= 5:
                    decision = "critical"
                    confidence = max(confidence, 0.99)
                    reason = "icmp_echo_burst"
                else:
                    reason = "icmp_echo_request"

        event = MonitorEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            src_ip=src_ip,
            dst_ip=dst_ip,
            protocol=proto,
            decision=decision,
            confidence=round(confidence, 6),
            reason=reason,
            length=length,
            src_port=src_port,
            dst_port=dst_port,
        )
        event_dict = event.__dict__
        with self._lock:
            self._events.append(event_dict)
            # update metrics
            minute = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
            self._metrics[minute]["total"] += 1
            if event_dict.get("decision") in ["attack", "critical", "risk"]:
                self._metrics[minute]["attacks"] += 1
                self._attack_alert_counter += 1
                if self._attack_alert_counter >= self._alert_threshold:
                    self._trigger_email_alert()
                    self._attack_alert_counter = 0

            self._total_processed += 1
        self._save_event_to_disk(event_dict)

    def ingest_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Ingest a list of flow records, run predictions, store events to disk and update metrics.

        This is designed for high-throughput batch uploads.
        """
        if not records:
            return {"count": 0}

        try:
            preds = self.predictor.predict_batch(records)
        except Exception as exc:
            return {"count": 0, "error": str(exc)}

        created = 0
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            for rec, pred in zip(records, preds):
                src_ip = rec.get("src_ip") or rec.get("saddr") or "-"
                dst_ip = rec.get("dst_ip") or rec.get("daddr") or "-"
                proto = rec.get("proto", "-")
                event = MonitorEvent(
                    timestamp=now_iso,
                    src_ip=str(src_ip),
                    dst_ip=str(dst_ip),
                    protocol=str(proto),
                    decision=pred.get("decision", "normal"),
                    confidence=float(pred.get("confidence", 0.0)),
                    reason="batch_ingest",
                )
                event_dict = event.__dict__
                self._events.append(event_dict)
                self._save_event_to_disk(event_dict)
                minute = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
                self._metrics[minute]["total"] += 1
                if event_dict.get("decision") in ["attack", "critical", "risk"]:
                    self._metrics[minute]["attacks"] += 1
                    self._attack_alert_counter += 1
                    if self._attack_alert_counter >= self._alert_threshold:
                        self._trigger_email_alert()
                        self._attack_alert_counter = 0
                
                created += 1
                self._total_processed += 1

        return {"count": created}

    def get_metrics(self, minutes: int = 60) -> dict[str, Any]:
        """Return recent metrics for the last `minutes` minutes.

        Returns a dict with per-minute buckets (ISO minute string) and totals.
        """
        now = datetime.now(timezone.utc)
        buckets: list[str] = []
        for i in range(minutes):
            t = now - timedelta(minutes=i)
            buckets.append(t.strftime("%Y-%m-%dT%H:%M"))

        data = {b: self._metrics.get(b, {"total": 0, "attacks": 0}) for b in reversed(buckets)}
        total_events = sum(v["total"] for v in data.values())
        total_attacks = sum(v["attacks"] for v in data.values())
        return {"per_minute": data, "total_events": total_events, "total_attacks": total_attacks}

    def _trigger_email_alert(self) -> None:
        """Offload email sending to the executor."""
        if not self.smtp_config["enabled"]:
            return
        
        # Capture current stats for the email
        stats = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_processed": self._total_processed,
        }
        self._executor.submit(self._send_email_alert, stats)

    def _send_email_alert(self, stats: dict[str, Any]) -> None:
        """Synchronous SMTP send logic."""
        cfg = self.smtp_config
        try:
            msg = MIMEMultipart()
            msg['From'] = cfg['user']
            msg['To'] = cfg['recipient']
            msg['Subject'] = f"🛡️ Kaavach Alert: {self._alert_threshold} New Attacks Detected"

            body = f"""
            <h2>Kaavach IDS Security Alert</h2>
            <p>Your IDS system has detected a cluster of attacks.</p>
            <ul>
                <li><b>Alert Time:</b> {stats['time']}</li>
                <li><b>Attack Count:</b> {self._alert_threshold}</li>
                <li><b>Total Packets Analyzed:</b> {stats['total_processed']}</li>
            </ul>
            <p>Please check your dashboard for details on the source IPs and threat levels.</p>
            """
            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(cfg['host'], cfg['port'])
            server.starttls()
            server.login(cfg['user'], cfg['pass'])
            server.send_message(msg)
            server.quit()
            print(f"✅ Security Alert Email Sent to {cfg['recipient']}")
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
