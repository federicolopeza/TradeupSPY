from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple, Iterable

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

    def _get_with_retries(self, path: str, params: Dict[str, Any], retries: int = 4) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """GET con reintentos que devuelve (data_normalizada, headers).

        - Normaliza listas a {"data": list} para uso interno consistente.
        - Aplica backoff exponencial y respeta 'retry-after' en 429.
        """
        url = f"{self.base_url}{path}"
        backoffs = [0.5, 1.0, 2.0, 4.0]
        for attempt in range(retries):
            try:
                resp = self.session.get(url, headers=self._headers(), params=params, timeout=self.timeout)
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("retry-after", backoffs[min(attempt, len(backoffs)-1)]))
                    time.sleep(retry_after)
                    continue
                if 500 <= resp.status_code < 600:
                    time.sleep(backoffs[min(attempt, len(backoffs)-1)])
                    continue
                resp.raise_for_status()
                data_raw = resp.json()
                if isinstance(data_raw, dict) and "data" in data_raw:
                    return data_raw, dict(resp.headers)
                if isinstance(data_raw, list):
                    return {"data": data_raw}, dict(resp.headers)
                return data_raw, dict(resp.headers)
            except Exception:
                time.sleep(backoffs[min(attempt, len(backoffs)-1)])
                continue
        # intento final
        resp = self.session.get(url, headers=self._headers(), params=params, timeout=self.timeout)
        resp.raise_for_status()
        data_raw = resp.json()
        if isinstance(data_raw, dict) and "data" in data_raw:
            return data_raw, dict(resp.headers)
        if isinstance(data_raw, list):
            return {"data": data_raw}, dict(resp.headers)
        return data_raw, dict(resp.headers)

    @staticmethod
    def _extract_next_cursor(headers: Dict[str, str], data: Dict[str, Any]) -> Optional[str]:
        """Extrae cursor de siguiente página desde headers o cuerpo.

        - Prefiere header 'X-Next-Cursor' (case-insensitive).
        - Fallback: campo 'cursor' en el JSON si existe y es string.
        """
        # headers case-insensitive lookup
        for k, v in headers.items():
            if k.lower() == "x-next-cursor" and v:
                return v
        if isinstance(data, dict):
            cursor = data.get("cursor")
            if isinstance(cursor, str) and cursor:
                return cursor
        return None

    def iter_listings(self, **filters: Any) -> Iterable[Dict[str, Any]]:
        """Itera sobre listados paginando con cursor cuando esté disponible.

        Uso típico:
            for item in client.iter_listings(market_hash_name="AK-47 | Redline (Field-Tested)", sort_by="lowest_price", limit=50):
                ...

        Notas:
        - Si el backend no provee cursor, se devolverá solo la primera página.
        - Respeta 'limit' enviado por el caller.
        """
        params: Dict[str, Any] = dict(filters)
        cursor: Optional[str] = params.get("cursor")
        while True:
            if cursor:
                params["cursor"] = cursor
            data, headers = self._get_with_retries("/api/v1/listings", params)
            items = data.get("data") or []
            if not isinstance(items, list):
                # Si el backend devolviera un objeto, tratar de encontrar 'data' lista
                items = []
            for it in items:
                yield it
            # siguiente página
            next_cursor = self._extract_next_cursor(headers, data)
            if not next_cursor:
                break
            cursor = next_cursor

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
        data, _headers = self._get_with_retries("/api/v1/listings", params)
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
