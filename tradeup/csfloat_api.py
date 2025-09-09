from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

# Load .env once (safe if called multiple times)
load_dotenv(override=False)

# CSFloat API base (read after loading .env)
BASE_URL = os.getenv("CSFLOAT_BASE", "https://csfloat.com")


def get_api_key() -> Optional[str]:
    return os.getenv("CSFLOAT_API_KEY")


def build_market_hash_name(name: str, wear_name: str, stattrak: bool) -> str:
    """Construct Steam market_hash_name like:
    - "AK-47 | Cartel (Field-Tested)"
    - "StatTrak™ AK-47 | Cartel (Field-Tested)"
    """
    prefix = "StatTrak™ " if stattrak else ""
    return f"{prefix}{name} ({wear_name})"


class CsfloatClient:
    """Minimal CSFloat client for GET /api/v1/listings.

    Note: All prices are in cents.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: float = 15.0) -> None:
        self.api_key = api_key or get_api_key()
        self.base_url = base_url or BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        self._cache: Dict[Tuple[str, int], Optional[int]] = {}

    def _headers(self) -> Dict[str, str]:
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["authorization"] = self.api_key
        return headers

    def _request_with_retries(self, path: str, params: Dict[str, Any], retries: int = 4) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        backoffs = [0.5, 1.0, 2.0, 4.0]
        last_err: Optional[Exception] = None
        for attempt in range(retries):
            try:
                resp = self.session.get(url, headers=self._headers(), params=params, timeout=self.timeout)
                if resp.status_code == 429:
                    # rate limited, check retry-after or backoff
                    retry_after = float(resp.headers.get("retry-after", backoffs[min(attempt, len(backoffs)-1)]))
                    time.sleep(retry_after)
                    continue
                if 500 <= resp.status_code < 600:
                    time.sleep(backoffs[min(attempt, len(backoffs)-1)])
                    continue
                resp.raise_for_status()
                data = resp.json()
                # normalize expected shape
                if isinstance(data, dict) and "data" in data:
                    return data
                if isinstance(data, list):
                    return {"data": data}
                return data
            except Exception as e:  # broad catch to retry on network issues
                last_err = e
                time.sleep(backoffs[min(attempt, len(backoffs)-1)])
                continue
        # final attempt without catching to propagate
        resp = self.session.get(url, headers=self._headers(), params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data
        if isinstance(data, list):
            return {"data": data}
        return data

    def get_lowest_price_cents(self, market_hash_name: str, stattrak: bool) -> Optional[int]:
        """Return lowest listing price in cents for a given market_hash_name.

        The API supports filtering by market_hash_name and category:
        - category: 1 normal, 2 stattrak, 3 souvenir
        """
        category = 2 if stattrak else 1
        cache_key = (market_hash_name, category)
        if cache_key in self._cache:
            return self._cache[cache_key]

        params: Dict[str, Any] = {
            "sort_by": "lowest_price",
            "market_hash_name": market_hash_name,
            "limit": 50,
            "category": category,
        }
        data = self._request_with_retries("/api/v1/listings", params)
        items = data.get("data") or []
        lowest: Optional[int] = None
        for it in items:
            # Support both raw API and proxied normalized shape
            price = it.get("price") if isinstance(it, dict) else None
            if price is None:
                continue
            if lowest is None or price < lowest:
                lowest = price
        self._cache[cache_key] = lowest
        return lowest


__all__ = [
    "CsfloatClient",
    "build_market_hash_name",
]
