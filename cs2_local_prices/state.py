from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .models import StateModel


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.model = StateModel()
        self._loaded = False

    def load(self) -> None:
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self.model = StateModel(**data)
            except Exception:
                # Start with empty state if corrupted
                self.model = StateModel()
        else:
            self.model = StateModel()
        self._loaded = True

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.model.timestamp = time.time()
        tmp_fd, tmp_name = tempfile.mkstemp(prefix="state_", suffix=".json", dir=str(self.path.parent))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmpf:
                json.dump(self.model.model_dump(), tmpf, ensure_ascii=False, separators=(",", ":"))
                tmpf.flush()
                os.fsync(tmpf.fileno())
            os.replace(tmp_name, self.path)
        finally:
            try:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except Exception:
                pass

    def set_pending(self, mhns: List[str]) -> None:
        self.model.pending = list(mhns)
        self.model.cursor = 0
        self.model.retry_queue = []
        self.save()

    def next_pending(self) -> str | None:
        if self.model.cursor < len(self.model.pending):
            return self.model.pending[self.model.cursor]
        return None

    def advance_cursor(self) -> None:
        self.model.cursor += 1
        self.save()

    def mark_processed(self, mhn: str) -> None:
        self.model.processed.append(mhn)
        self.save()

    def add_retry(self, mhn: str) -> None:
        if mhn not in self.model.retry_queue:
            self.model.retry_queue.append(mhn)
            self.save()
