from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional, Tuple

import httpx

from .config import AppConfig
from .logging_setup import get_logger

logger = get_logger(__name__)


def parse_retry_after(value: str) -> Optional[float]:
    try:
        # Could be delta-seconds
        secs = float(value)
        if secs >= 0:
            return secs
    except Exception:
        pass
    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            # Normalize now to dt's timezone
            now = datetime.now(dt.tzinfo or timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
            delta = (dt - now).total_seconds()
            return max(0.0, delta)
    except Exception:
        return None
    return None


def to_cents(price: Any) -> Optional[int]:
    # Accept integer cents or float USD
    if price is None:
        return None
    if isinstance(price, (int,)):
        return int(price)
    if isinstance(price, float):
        if price != price:  # NaN check
            return None
        return int(round(price * 100))
    if isinstance(price, str):
        s = price.strip().replace("$", "")
        try:
            if "." in s:
                return int(round(float(s) * 100))
            return int(s)
        except Exception:
            return None
    return None


def extract_lowest_price(json_data: Dict[str, Any]) -> Optional[int]:
    # Expect something like {'listings': [{... 'price': 12.34 or 1234}]}
    # But be robust to alternative keys.
    listings = None
    for key in ("listings", "data", "results"):
        if isinstance(json_data.get(key), list):
            listings = json_data[key]
            break
    if not listings:
        return None
    min_cents: Optional[int] = None
    for item in listings:
        # Try multiple price fields
        for k in ("price_cents", "price", "price_usd", "lowest_price", "raw_price"):
            if k in item:
                cents = to_cents(item[k])
                if cents is not None:
                    if min_cents is None or cents < min_cents:
                        min_cents = cents
        # Some APIs nest under item['pricing']
        if "pricing" in item and isinstance(item["pricing"], dict):
            for k in ("price_cents", "price", "price_usd"):
                if k in item["pricing"]:
                    cents = to_cents(item["pricing"][k])
                    if cents is not None:
                        if min_cents is None or cents < min_cents:
                            min_cents = cents
    return min_cents


class CSFloatClient:
    def __init__(self, cfg: AppConfig, transport: Optional[httpx.BaseTransport] = None) -> None:
        self.cfg = cfg
        self.client = httpx.AsyncClient(
            base_url=cfg.csfloat_api_base,
            timeout=httpx.Timeout(cfg.timeout_seconds, read=cfg.timeout_seconds, write=cfg.timeout_seconds),
            headers={
                "Accept": "application/json",
                **({"Authorization": f"Bearer {cfg.csfloat_api_key}"} if cfg.csfloat_api_key else {}),
            },
            transport=transport,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def fetch_lowest_price(self, mhn: str) -> Tuple[Optional[int], Dict[str, Any]]:
        """Fetch lowest price in cents for the given MarketHashName.

        Returns (price_cents or None, meta dict with status/latency/retries)
        """
        meta: Dict[str, Any] = {"retries": 0, "status": None, "latency_ms": 0.0}
        params = {
            "sort_by": "lowest_price",
            "market_hash_name": mhn,
            "limit": str(self.cfg.max_pages * 50),
            "category": "1",
        }
        attempt = 0
        backoff = self.cfg.backoff_initial_seconds
        start_ts = time.time()
        while True:
            attempt += 1
            try:
                t0 = time.time()
                resp = await self.client.get("/api/v1/listings", params=params)
                latency = (time.time() - t0) * 1000.0
                meta["latency_ms"] = latency
                meta["status"] = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    cents = extract_lowest_price(data)
                    return cents, meta
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after is not None:
                        sleep_s = parse_retry_after(retry_after) or backoff
                    else:
                        sleep_s = min(self.cfg.backoff_max_seconds, backoff)
                        # full jitter
                        sleep_s = random.uniform(0, sleep_s)
                        backoff = min(self.cfg.backoff_max_seconds, backoff * 2)
                    meta["retries"] += 1
                    await asyncio.sleep(sleep_s)
                    continue
                if 500 <= resp.status_code < 600:
                    sleep_s = random.uniform(0, min(self.cfg.backoff_max_seconds, backoff))
                    backoff = min(self.cfg.backoff_max_seconds, backoff * 2)
                    meta["retries"] += 1
                    await asyncio.sleep(sleep_s)
                    continue
                # Other statuses: do not retry
                return None, meta
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError, httpx.ConnectError):
                sleep_s = random.uniform(0, min(self.cfg.backoff_max_seconds, backoff))
                backoff = min(self.cfg.backoff_max_seconds, backoff * 2)
                meta["retries"] += 1
                await asyncio.sleep(sleep_s)
                continue
            except Exception:
                return None, meta
            finally:
                if time.time() - start_ts > self.cfg.timeout_seconds * 4:
                    # Stop after a global budget to prevent livelock
                    break
        return None, meta
