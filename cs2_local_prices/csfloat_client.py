from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional, Tuple, Iterable

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
    """Extrae el menor precio (en centavos) de posibles estructuras JSON.

    Soporta múltiples variantes observadas en APIs públicas:
    - Top-level: lowest_price, lowest_price_cents
    - Listas bajo: listings, data, results
    - Campos de precio en item: price_cents, priceCents, price, price_usd, price_usd_cents,
      lowest_price, raw_price, converted_price, converted_price_cents
    - Niveles anidados: item["pricing"][...]
    """

    # 1) Revisar top-level
    for k in ("lowest_price_cents", "lowest_price", "price_cents", "price"):
        if k in json_data:
            c = to_cents(json_data.get(k))
            if c is not None:
                return c

    # 2) Determinar colección de listings
    listings = None
    for key in ("listings", "data", "results"):
        if isinstance(json_data.get(key), list):
            listings = json_data[key]
            break
    if not listings:
        return None

    def iter_candidate_prices(obj: Dict[str, Any]) -> Iterable[Optional[int]]:
        # Campos directos
        for k in (
            "price_cents",
            "priceCents",
            "price_usd_cents",
            "converted_price_cents",
            "price",
            "price_usd",
            "converted_price",
            "lowest_price",
            "raw_price",
        ): 
            if k in obj:
                yield to_cents(obj.get(k))
        # Campos anidados conocidos
        pricing = obj.get("pricing")
        if isinstance(pricing, dict):
            for k in ("price_cents", "price", "price_usd", "price_usd_cents"):
                if k in pricing:
                    yield to_cents(pricing.get(k))

    min_cents: Optional[int] = None
    for item in listings:
        if not isinstance(item, dict):
            continue
        for cents in iter_candidate_prices(item):
            if cents is None:
                continue
            if min_cents is None or cents < min_cents:
                min_cents = cents
    return min_cents


class CSFloatClient:
    def __init__(self, cfg: AppConfig, transport: Optional[httpx.BaseTransport] = None) -> None:
        self.cfg = cfg
        # Build headers according to auth style expected by CSFloat
        base_headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "cs2-local-prices/0.1 (+https://github.com/falopp/TradeupSPY)",
        }
        if cfg.csfloat_api_key:
            style = (cfg.auth_style or "both").lower()
            if style in ("bearer", "both"):
                base_headers["Authorization"] = f"Bearer {cfg.csfloat_api_key}"
            if style in ("raw", "both"):
                # Some deployments expect the raw token in the Authorization header without Bearer
                # Using lowercase key to avoid overwriting the Bearer entry in case-insensitive dicts
                base_headers["authorization"] = cfg.csfloat_api_key

        self.client = httpx.AsyncClient(
            base_url=cfg.csfloat_api_base,
            timeout=httpx.Timeout(cfg.timeout_seconds, read=cfg.timeout_seconds, write=cfg.timeout_seconds),
            headers=base_headers,
            transport=transport,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def fetch_lowest_price(self, mhn: str) -> Tuple[Optional[int], Dict[str, Any]]:
        """Fetch lowest price in cents for the given MarketHashName.

        Returns (price_cents or None, meta dict with status/latency/retries)
        """
        meta: Dict[str, Any] = {"retries": 0, "status": None, "latency_ms": 0.0}
        base_params = {
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
                # Try a set of parameter variants to accommodate API differences
                variants = []
                variants.append(base_params)
                # v1: without category
                p_no_cat = dict(base_params)
                p_no_cat.pop("category", None)
                variants.append(p_no_cat)
                # v2: without sort_by
                p_no_sort = dict(p_no_cat)
                p_no_sort.pop("sort_by", None)
                variants.append(p_no_sort)
                # v3: use 'name' instead of 'market_hash_name'
                p_name = dict(p_no_sort)
                mh = p_name.pop("market_hash_name", mhn)
                p_name["name"] = mh
                variants.append(p_name)

                last_resp = None
                for vp in variants:
                    resp = await self.client.get("/api/v1/listings", params=vp)
                    last_resp = resp
                    latency = (time.time() - t0) * 1000.0
                    meta["latency_ms"] = latency
                    meta["status"] = resp.status_code
                    if resp.status_code == 200:
                        data = resp.json()
                        cents = extract_lowest_price(data)
                        if cents is None:
                            # Instrumentación: loguear forma del payload para diagnóstico
                            try:
                                top_keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
                                sample_keys = []
                                listings = None
                                for lk in ("listings", "data", "results"):
                                    if isinstance(data, dict) and isinstance(data.get(lk), list):
                                        listings = data.get(lk)
                                        break
                                if isinstance(listings, list) and listings:
                                    first = listings[0]
                                    if isinstance(first, dict):
                                        sample_keys = list(first.keys())[:20]
                                logger.debug(
                                    "No price extracted for MHN=%s. top_keys=%s sample_item_keys=%s",
                                    mhn,
                                    top_keys,
                                    sample_keys,
                                )
                            except Exception:
                                pass
                            # Probar siguiente variante
                            continue
                        # Precio encontrado, retornar
                        return cents, meta
                    if resp.status_code in (400, 403):
                        # Try next variant immediately
                        continue
                    # break to outer handling for 429/5xx/others
                    break

                # If we exhausted variants with 200 (sin precio) o 400/403, treat as failure for this MHN
                if last_resp is not None and last_resp.status_code in (200, 400, 403):
                    return None, meta
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
