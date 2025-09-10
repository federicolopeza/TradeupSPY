from __future__ import annotations

import asyncio
import glob
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from .cache import JSONCache, PriceCache, SQLiteCache
from .catalog import read_catalog
from .config import AppConfig
from .csfloat_client import CSFloatClient
from .logging_setup import get_logger
from .metrics import Metrics
from .mhn import build_mhn, dedupe_sorted, parse_mhn
from .models import PriceRecordA, PriceRecordB, SchemaOption, StatTrakMode
from .state import StateStore
from .wears import valid_wears_for_range
from .writer import CSVWriter

logger = get_logger(__name__)


class TokenBucket:
    """Enforce a minimum interval between requests across workers.

    This simple rate limiter ensures at least `interval` seconds elapse between
    successive acquisitions, regardless of concurrency.
    """

    def __init__(self, interval_seconds: float) -> None:
        self.interval = interval_seconds
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.time()
            # If first use, allow immediately and set last
            if self._last == 0.0:
                self._last = now
                return
            elapsed = now - self._last
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
                self._last = time.time()
            else:
                self._last = now


@dataclass
class BuilderResult:
    total: int
    resolved: int
    failed: int


class PriceBuilder:
    def __init__(self, cfg: AppConfig, client: Optional[CSFloatClient] = None) -> None:
        self.cfg = cfg
        self.cache: PriceCache
        if str(cfg.cache_store).endswith(".sqlite") or str(cfg.cache_store).endswith(".sqlite3"):
            self.cache = SQLiteCache(cfg.cache_store)
        else:
            self.cache = JSONCache(cfg.cache_store)
        self.state = StateStore(cfg.resume_state)
        self.metrics = Metrics()
        self.client = client
        self.token_bucket = TokenBucket(cfg.effective_interval_seconds())
        self._io_lock = asyncio.Lock()

    def derive_mhns_from_catalog(self) -> List[str]:
        rows = read_catalog(self.cfg.catalog)
        mhns: List[str] = []
        target_rarities = set(self.cfg.rarities)
        for r in rows:
            if r.Grado not in target_rarities:
                continue
            wears = valid_wears_for_range(r.FloatMin, r.FloatMax)
            for w in wears:
                if self.cfg.st_mode in (StatTrakMode.both, StatTrakMode.nost):
                    mhns.append(build_mhn(r.Arma, w, False))
                if self.cfg.st_mode in (StatTrakMode.both, StatTrakMode.st):
                    mhns.append(build_mhn(r.Arma, w, True))
        mhns = dedupe_sorted(mhns)
        if self.cfg.limit and self.cfg.limit > 0:
            mhns = mhns[: self.cfg.limit]
        return mhns

    def shrink_by_contracts(self, mhns: List[str]) -> List[str]:
        pattern = self.cfg.only_from_contracts
        if not pattern:
            return mhns
        matched_files: List[str] = []
        for p in glob.glob(pattern, recursive=True):
            matched_files.append(p)
        if not matched_files:
            logger.warning("only_from_contracts matched no files: %s", pattern)
            return mhns
        needed: Set[str] = set()
        import csv

        for file in matched_files:
            try:
                with open(file, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            name = (row.get("Name") or "").strip()
                            flt = float(row.get("Float") or 0.0)
                            st_raw = (row.get("StatTrak") or "false").strip().lower()
                            st = st_raw == "true"
                            from .wears import wear_from_float

                            wear = wear_from_float(flt)
                            needed.add(build_mhn(name, wear, st))
                        except Exception:
                            continue
            except Exception:
                continue
        shrink = [m for m in mhns if m in needed]
        return dedupe_sorted(shrink)

    def build_pending_set(self) -> List[str]:
        base = self.derive_mhns_from_catalog()
        if self.cfg.only_from_contracts:
            base = self.shrink_by_contracts(base)
        # remove any already cached
        out = [m for m in base if not self.cache.contains(m)]
        return out

    def _prepopulate_from_cache(self, base_mhns: List[str]) -> None:
        """Write cached prices to CSV for MHNs in base set (idempotent)."""
        cached_records: List[PriceRecordA | PriceRecordB] = []
        for m in base_mhns:
            if not self.cache.contains(m):
                continue
            price = self.cache.get(m)
            if price is None:
                continue
            name, wear, st = parse_mhn(m)
            if self.cfg.schema == SchemaOption.A:
                cached_records.append(
                    PriceRecordA(Name=name, Wear=wear, PriceCents=int(price), StatTrak=st)
                )
            else:
                cached_records.append(PriceRecordB(MarketHashName=m, PriceCents=int(price)))
        if cached_records:
            writer = CSVWriter(self.cfg.out_csv, self.cfg.schema)
            writer.append_records(cached_records)

    async def _worker(self, idx: int, queue: asyncio.Queue[str], client: CSFloatClient) -> None:
        while True:
            try:
                mhn = await queue.get()
            except asyncio.CancelledError:
                return
            if mhn is None:  # type: ignore
                queue.task_done()
                return
            await self.token_bucket.acquire()
            t_req = time.time()
            self.metrics.record_request(t_req)
            price_cents, meta = await client.fetch_lowest_price(mhn)
            self.metrics.record_latency(meta.get("latency_ms", 0.0))
            if meta.get("status") == 429:
                self.metrics.total_429 += 1
            self.metrics.total_seen += 1

            async with self._io_lock:
                if price_cents is not None and isinstance(price_cents, int):
                    # Persist
                    self.cache.set(mhn, price_cents)
                    name, wear, st = parse_mhn(mhn)
                    if self.cfg.schema == SchemaOption.A:
                        rec = PriceRecordA(Name=name, Wear=wear, PriceCents=price_cents, StatTrak=st)
                    else:
                        rec = PriceRecordB(MarketHashName=mhn, PriceCents=price_cents)
                    writer = CSVWriter(self.cfg.out_csv, self.cfg.schema)
                    writer.append_records([rec])
                    self.metrics.total_resolved += 1
                else:
                    self.metrics.total_failed += 1
                    # Add to retry queue
                    self.state.add_retry(mhn)
                    if len(self.metrics.unresolved_sample) < 20:
                        self.metrics.unresolved_sample.append(mhn)

                self.state.mark_processed(mhn)
                self.state.advance_cursor()
            # Periodic flush
            if (self.metrics.total_seen % 10) == 0:
                async with self._io_lock:
                    self.cache.flush()
                    self.metrics.export_atomic(self.cfg.metrics_out)
                    self.state.save()
            queue.task_done()

    async def run(self) -> BuilderResult:
        # Prepare state
        self.state.load()
        pending: List[str]
        if not self.state.model.pending:
            base = self.derive_mhns_from_catalog()
            if self.cfg.only_from_contracts:
                base = self.shrink_by_contracts(base)
            # Prepopulate CSV from cache for base universe
            self._prepopulate_from_cache(base)
            # Now compute pending (excluding cached)
            pending = [m for m in base if not self.cache.contains(m)]
            # Initialize state deterministically
            self.state.set_pending(pending)
        else:
            pending = self.state.model.pending
        # Apply cursor (resume)
        cursor = self.state.model.cursor
        remaining = pending[cursor:]
        if not remaining:
            logger.info("No pending MHNs. Nothing to do.")
            return BuilderResult(total=0, resolved=0, failed=0)

        # Create client if not provided
        client = self.client or CSFloatClient(self.cfg)

        queue: asyncio.Queue[str] = asyncio.Queue()
        for m in remaining:
            await queue.put(m)
        # Add sentinels for workers
        for _ in range(self.cfg.concurrency):
            await queue.put(None)  # type: ignore

        # Spawn workers
        workers = [asyncio.create_task(self._worker(i, queue, client)) for i in range(self.cfg.concurrency)]

        # Early stop after safe_stop_after successes
        async def monitor_stop() -> None:
            if self.cfg.safe_stop_after is None:
                return
            target = int(self.cfg.safe_stop_after)
            while self.metrics.total_resolved < target and any(not w.done() for w in workers):
                await asyncio.sleep(0.1)
            # Cancel remaining tasks by draining the queue
            while not queue.empty():
                try:
                    queue.get_nowait()
                    queue.task_done()
                except asyncio.QueueEmpty:
                    break
            for w in workers:
                w.cancel()

        monitor_task = asyncio.create_task(monitor_stop())
        try:
            await queue.join()
        except KeyboardInterrupt:
            logger.warning("Interrupted. Flushing state and metrics...")
        finally:
            for w in workers:
                if not w.done():
                    w.cancel()
            if not monitor_task.done():
                monitor_task.cancel()
            self.cache.flush()
            self.metrics.export_atomic(self.cfg.metrics_out)
            self.state.save()
            await client.close()

        return BuilderResult(
            total=self.metrics.total_seen,
            resolved=self.metrics.total_resolved,
            failed=self.metrics.total_failed,
        )
