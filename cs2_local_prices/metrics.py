from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class Metrics:
    total_seen: int = 0
    total_resolved: int = 0
    total_failed: int = 0
    total_429: int = 0
    total_retries: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    request_timestamps: List[float] = field(default_factory=list)
    unresolved_sample: List[str] = field(default_factory=list)

    def record_request(self, when_ts: float) -> None:
        self.request_timestamps.append(when_ts)
        # keep last 1000 to bound memory
        if len(self.request_timestamps) > 1000:
            self.request_timestamps = self.request_timestamps[-1000:]

    def record_latency(self, ms: float) -> None:
        self.latencies_ms.append(ms)
        if len(self.latencies_ms) > 1000:
            self.latencies_ms = self.latencies_ms[-1000:]

    def avg_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return sum(self.latencies_ms) / len(self.latencies_ms)

    def qps(self) -> float:
        # compute over last 60 seconds window
        now = time.time()
        window = [t for t in self.request_timestamps if now - t <= 60.0]
        self.request_timestamps = window
        return len(window) / 60.0 if window else 0.0

    def snapshot(self) -> Dict[str, object]:
        return {
            "total_seen": self.total_seen,
            "total_resolved": self.total_resolved,
            "total_failed": self.total_failed,
            "total_429": self.total_429,
            "total_retries": self.total_retries,
            "avg_latency_ms": self.avg_latency_ms(),
            "qps": self.qps(),
            "unresolved_sample": list(self.unresolved_sample)[:20],
        }

    def export_atomic(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(prefix="metrics_", suffix=".json", dir=str(path.parent))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self.snapshot(), f, ensure_ascii=False, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, path)
        finally:
            try:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except Exception:
                pass
