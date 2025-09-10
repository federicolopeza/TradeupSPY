from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional


class PriceCache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[int]:
        ...

    @abstractmethod
    def set(self, key: str, price_cents: int) -> None:
        ...

    @abstractmethod
    def contains(self, key: str) -> bool:
        ...

    @abstractmethod
    def size(self) -> int:
        ...

    @abstractmethod
    def flush(self) -> None:
        ...


class JSONCache(PriceCache):
    def __init__(self, path: Path) -> None:
        self.path = path
        self._store: Dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("cache file is malformed")
                # ensure int values
                self._store = {str(k): int(v) for k, v in data.items()}
            except Exception:
                # start fresh but do not delete file
                self._store = {}
        else:
            self._store = {}

    def _atomic_write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(prefix="cache_", suffix=".json", dir=str(self.path.parent))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmpf:
                json.dump(self._store, tmpf, ensure_ascii=False, separators=(",", ":"))
                tmpf.flush()
                os.fsync(tmpf.fileno())
            os.replace(tmp_name, self.path)
        finally:
            try:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except Exception:
                pass

    def get(self, key: str) -> Optional[int]:
        return self._store.get(key)

    def set(self, key: str, price_cents: int) -> None:
        self._store[key] = int(price_cents)

    def contains(self, key: str) -> bool:
        return key in self._store

    def size(self) -> int:
        return len(self._store)

    def flush(self) -> None:
        self._atomic_write()


class SQLiteCache(PriceCache):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS prices (key TEXT PRIMARY KEY, price_cents INTEGER NOT NULL)"
        )
        self._conn.commit()

    def get(self, key: str) -> Optional[int]:
        cur = self._conn.execute("SELECT price_cents FROM prices WHERE key = ?", (key,))
        row = cur.fetchone()
        return int(row[0]) if row else None

    def set(self, key: str, price_cents: int) -> None:
        self._conn.execute(
            "INSERT INTO prices(key, price_cents) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET price_cents=excluded.price_cents",
            (key, int(price_cents)),
        )
        self._conn.commit()

    def contains(self, key: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM prices WHERE key = ?", (key,))
        return cur.fetchone() is not None

    def size(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM prices")
        return int(cur.fetchone()[0])

    def flush(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
