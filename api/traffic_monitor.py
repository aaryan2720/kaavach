from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from inference import KaavachPredictor

try:
    from scapy.all import ICMP, IP, sniff  # type: ignore

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


class TrafficMonitor:
    def __init__(self, predictor: KaavachPredictor) -> None:
        self.predictor = predictor
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._events: deque[dict[str, Any]] = deque(maxlen=500)
        self._icmp_window: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=50))

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
        self._thread.start()
        self._running = True
        return {"started": True, "message": "Traffic monitor started."}

    def stop(self) -> dict[str, Any]:
        if not self._running:
            return {"stopped": True, "message": "Monitor already stopped."}

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._running = False
        return {"stopped": True, "message": "Traffic monitor stopped."}

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "backend": self.backend,
            "events_buffered": len(self._events),
        }

    def latest_events(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        return list(self._events)[-limit:]

    def _sniff_loop(self) -> None:
        while not self._stop_event.is_set():
            sniff(
                filter="ip",
                prn=self._handle_packet,
                store=False,
                timeout=1,
            )
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

        ttl = int(getattr(packet[IP], "ttl", 64))
        length = int(len(packet))

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

        pred = self.predictor.predict_one(features)

        reason = "model_inference"
        decision = pred["decision"]
        confidence = float(pred["confidence"])

        # Explicit ping detector: ICMP echo-request burst from same source.
        if ICMP in packet and int(packet[ICMP].type) == 8:
            q = self._icmp_window[src_ip]
            q.append(now_ts)
            while q and now_ts - q[0] > 10:
                q.popleft()
            if len(q) >= 5:
                decision = "attack"
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
        )
        self._events.append(event.__dict__)
