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

    Notas:
    - Todos los precios están en centavos.
    - Incluye caché en memoria con TTL opcional para consultas de precio mínimo por `market_hash_name`.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 15.0,
        ttl_seconds: Optional[float] = 300.0,
        max_pages: int = 3,
    ) -> None:
        self.api_key = api_key or get_api_key()
        self.base_url = base_url or BASE_URL
        self.timeout = timeout
        self.ttl_seconds = ttl_seconds
        self.max_pages = max_pages
        self.session = requests.Session()
        # cache key: (market_hash_name, category) -> (price_cents_or_None, expires_at_epoch_or_0)
        self._cache: Dict[Tuple[str, int], Tuple[Optional[int], float]] = {}

    def _headers(self) -> Dict[str, str]:
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["authorization"] = self.api_key
        return headers

    

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
        """Devuelve el menor precio listado en centavos para un `market_hash_name`.

        Implementación:
        - Usa `iter_listings()` con paginación por cursor hasta `max_pages` (por defecto 3).
        - Filtra por `market_hash_name` exacto cuando el backend lo provee en cada item.
        - Valida la categoría con StatTrak cuando esté disponible en el item.
        - Ignora precios faltantes o no positivos.
        - Aplica caché en memoria con TTL opcional configurada en el constructor.

        API params relevantes:
        - category: 1 normal, 2 stattrak, 3 souvenir
        """
        category = 2 if stattrak else 1
        cache_key = (market_hash_name, category)
        # cache hit con TTL válida
        cached = self._cache.get(cache_key)
        now = time.time()
        if cached is not None:
            value, expires_at = cached
            if expires_at == 0 or expires_at > now:
                return value

        params: Dict[str, Any] = {
            "sort_by": "lowest_price",
            "market_hash_name": market_hash_name,
            "limit": 50,
            "category": category,
        }

        lowest: Optional[int] = None
        taken = 0
        page_item_cap = params["limit"] * max(1, int(self.max_pages))
        for it in self.iter_listings(**params):
            taken += 1
            if taken > page_item_cap:
                break
            if not isinstance(it, dict):
                continue
            # precio
            price = it.get("price")
            if price is None or not isinstance(price, (int, float)):
                continue
            price_int = int(price)
            if price_int <= 0:
                continue
            # validar MHN si viene en el item
            mhn_item = it.get("market_hash_name") or it.get("name")
            if isinstance(mhn_item, str) and mhn_item and mhn_item != market_hash_name:
                continue
            # validar categoría/stattrak si se expone
            item_category = it.get("category")
            if isinstance(item_category, int) and item_category not in (1, 2, 3):
                # categoría inesperada -> ignorar
                continue
            if isinstance(item_category, int) and item_category != category:
                continue
            item_st = it.get("stattrak")
            if isinstance(item_st, bool) and (item_st != stattrak):
                continue

            if lowest is None or price_int < lowest:
                lowest = price_int

        # guardar en caché (respeta TTL si se configuró, 0 = sin expiración)
        expires_at = 0.0 if self.ttl_seconds in (None, 0) else now + float(self.ttl_seconds)
        self._cache[cache_key] = (lowest, expires_at)
        return lowest


__all__ = [
    "CsfloatClient",
    "build_market_hash_name",
]
